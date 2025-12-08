#!/usr/bin/env python3
"""
Multi-namespace observability pipeline
Collects logs, metrics, and events from all 19 industries
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import psycopg2
from kafka import KafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ObservabilityPipeline:
    """Collects observability data from all namespaces"""
    
    def __init__(self):
        self.namespaces = [
            'finance', 'healthcare', 'automotive', 'retail', 'logistics',
            'energy', 'telecom', 'banking', 'insurance', 'manufacturing',
            'gov', 'education', 'cloud', 'media', 'aiplatform',
            'semiconductor', 'aicloud', 'gpucloud', 'socialmedia'
        ]
        self.k8s_client = self._init_k8s()
        self.kafka_producer = self._init_kafka()
        self.db_conn = self._init_db()
    
    def _init_k8s(self):
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        return {
            'core': client.CoreV1Api(),
            'apps': client.AppsV1Api(),
            'metrics': client.CustomObjectsApi()
        }
    
    def _init_kafka(self):
        try:
            return KafkaProducer(
                bootstrap_servers=os.getenv('KAFKA_BROKERS', 'localhost:9092').split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except Exception as e:
            logger.warning(f"Kafka init failed: {e}")
            return None
    
    def _init_db(self):
        try:
            return psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5433'),
                database=os.getenv('POSTGRES_DB', 'devops_brain'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres')
            )
        except Exception as e:
            logger.warning(f"DB init failed: {e}")
            return None
    
    def collect_pod_metrics(self, namespace: str) -> List[Dict]:
        """Collect pod metrics from a namespace"""
        metrics = []
        try:
            pods = self.k8s_client['core'].list_namespaced_pod(namespace)
            for pod in pods.items:
                metrics.append({
                    'namespace': namespace,
                    'pod': pod.metadata.name,
                    'status': pod.status.phase,
                    'restarts': sum(c.restart_count for c in pod.status.container_statuses or []),
                    'timestamp': datetime.utcnow().isoformat()
                })
        except ApiException as e:
            logger.error(f"Error collecting metrics from {namespace}: {e}")
        return metrics
    
    def collect_deployment_metrics(self, namespace: str) -> List[Dict]:
        """Collect deployment metrics from a namespace"""
        metrics = []
        try:
            deployments = self.k8s_client['apps'].list_namespaced_deployment(namespace)
            for dep in deployments.items:
                metrics.append({
                    'namespace': namespace,
                    'deployment': dep.metadata.name,
                    'replicas': dep.spec.replicas,
                    'ready': dep.status.ready_replicas or 0,
                    'available': dep.status.available_replicas or 0,
                    'timestamp': datetime.utcnow().isoformat()
                })
        except ApiException as e:
            logger.error(f"Error collecting deployment metrics from {namespace}: {e}")
        return metrics
    
    def collect_all_metrics(self):
        """Collect metrics from all namespaces"""
        all_metrics = []
        
        for namespace in self.namespaces:
            logger.info(f"Collecting metrics from {namespace}...")
            pod_metrics = self.collect_pod_metrics(namespace)
            dep_metrics = self.collect_deployment_metrics(namespace)
            all_metrics.extend(pod_metrics)
            all_metrics.extend(dep_metrics)
        
        return all_metrics
    
    def publish_metrics(self, metrics: List[Dict]):
        """Publish metrics to Kafka and database"""
        for metric in metrics:
            # Publish to Kafka
            if self.kafka_producer:
                self.kafka_producer.send('observability-metrics', value=metric)
            
            # Store in database
            if self.db_conn:
                self._store_metric(metric)
    
    def _store_metric(self, metric: Dict):
        """Store metric in database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO metrics (
                    namespace, metric_type, metric_data, timestamp
                ) VALUES (%s, %s, %s, %s)
            """, (
                metric.get('namespace'),
                metric.get('type', 'unknown'),
                json.dumps(metric),
                metric.get('timestamp', datetime.utcnow().isoformat())
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error storing metric: {e}")
            if self.db_conn:
                self.db_conn.rollback()
    
    def run(self):
        """Run the observability pipeline"""
        logger.info("🚀 Starting observability pipeline...")
        
        while True:
            try:
                metrics = self.collect_all_metrics()
                self.publish_metrics(metrics)
                logger.info(f"Collected {len(metrics)} metrics")
                time.sleep(60)  # Collect every minute
            except Exception as e:
                logger.error(f"Error in pipeline: {e}")
                time.sleep(60)

if __name__ == "__main__":
    pipeline = ObservabilityPipeline()
    pipeline.run()

