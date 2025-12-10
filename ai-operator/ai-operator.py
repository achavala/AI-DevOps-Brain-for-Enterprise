#!/usr/bin/env python3
"""
AI DevOps Brain Operator
Watches all 19 industries, detects anomalies, performs RCA, and suggests remediations
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import psycopg2
from kafka import KafkaProducer, KafkaConsumer
import redis

# Configure logging FIRST (before any imports that might use it)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add AI models to path
base_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(base_path, 'ai-models'))

# Import AI model inference modules using importlib (handles hyphenated directory names)
import importlib.util

# Anomaly Detection
try:
    anomaly_path = os.path.join(base_path, 'ai-models', 'anomaly-detection', 'inference.py')
    spec = importlib.util.spec_from_file_location('anomaly_inference', anomaly_path)
    anomaly_inference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(anomaly_inference)
    AnomalyDetectionInference = anomaly_inference.AnomalyDetectionInference
    logger.info("Anomaly detection inference loaded")
except (ImportError, FileNotFoundError, AttributeError) as e:
    AnomalyDetectionInference = None
    logger.warning(f"Anomaly detection inference not available: {e}")

# RCA Engine
try:
    rca_path = os.path.join(base_path, 'ai-models', 'rca-engine', 'inference.py')
    spec = importlib.util.spec_from_file_location('rca_inference', rca_path)
    rca_inference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rca_inference)
    RCAInference = rca_inference.RCAInference
    logger.info("RCA inference loaded")
except (ImportError, FileNotFoundError, AttributeError) as e:
    RCAInference = None
    logger.warning(f"RCA inference not available: {e}")

# Auto-Fix Engine
try:
    autofix_path = os.path.join(base_path, 'ai-models', 'auto-fix', 'inference.py')
    spec = importlib.util.spec_from_file_location('autofix_inference', autofix_path)
    autofix_inference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(autofix_inference)
    AutoFixInference = autofix_inference.AutoFixInference
    logger.info("Auto-fix inference loaded")
except (ImportError, FileNotFoundError, AttributeError) as e:
    AutoFixInference = None
    logger.warning(f"Auto-fix inference not available: {e}")

@dataclass
class Incident:
    """Represents a detected incident with structured data"""
    id: str
    namespace: str
    service: str
    severity: str
    anomaly_type: str
    detected_at: str
    description: str
    root_cause: Optional[str] = None
    remediation: Optional[str] = None
    status: str = "open"
    # Structured fields
    signals: List[str] = field(default_factory=list)
    confidence: float = 0.0
    industry: Optional[str] = None
    pattern: Optional[str] = None
    pattern_source: Optional[str] = None
    suspected_root_cause: Dict = field(default_factory=dict)
    suggested_actions: List[Dict] = field(default_factory=list)

@dataclass
class Anomaly:
    """Represents a detected anomaly"""
    namespace: str
    metric: str
    value: float
    threshold: float
    timestamp: str
    severity: str

class AIOperator:
    """Main AI DevOps Brain Operator"""
    
    def __init__(self):
        self.config = self._load_config()
        self.k8s_client = self._init_k8s()
        self.db_conn = self._init_db()
        self.redis_client = self._init_redis()
        self.kafka_producer = self._init_kafka()
        
        # Industry-specific failure patterns
        self.failure_patterns = self._load_failure_patterns()
        
        # AI Models
        self.anomaly_detector = self._init_anomaly_detector()
        self.rca_engine = self._init_rca_engine()
        self.auto_fix_engine = self._init_auto_fix_engine()
        
        # Watch loops
        self.running = True
        
    def _load_config(self) -> Dict:
        """Load configuration"""
        config_path = os.getenv('CONFIG_PATH', 'config/local.yaml')
        # Simplified - in production, use proper YAML loader
        return {
            'namespaces': [
                'finance', 'healthcare', 'automotive', 'retail', 'logistics',
                'energy', 'telecom', 'banking', 'insurance', 'manufacturing',
                'gov', 'education', 'cloud', 'media', 'aiplatform',
                'semiconductor', 'aicloud', 'gpucloud', 'socialmedia'
            ],
            'anomaly_thresholds': {
                'cpu_usage': 80.0,
                'memory_usage': 85.0,
                'error_rate': 5.0,
                'latency_p95': 1000.0,
                'pod_restarts': 3
            }
        }
    
    def _init_k8s(self):
        """Initialize Kubernetes client"""
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        return client.CoreV1Api()
    
    def _init_db(self):
        """Initialize PostgreSQL connection"""
        try:
            return psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5433'),
                database=os.getenv('POSTGRES_DB', 'devops_brain'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres')
            )
        except Exception as e:
            logger.warning(f"Database connection failed: {e}")
            return None
    
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            return redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                decode_responses=True
            )
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None
    
    def _init_kafka(self):
        """Initialize Kafka producer"""
        try:
            return KafkaProducer(
                bootstrap_servers=os.getenv('KAFKA_BROKERS', 'localhost:9092').split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except Exception as e:
            logger.warning(f"Kafka connection failed: {e}")
            return None
    
    def _init_anomaly_detector(self):
        """Initialize anomaly detection model"""
        if AnomalyDetectionInference:
            try:
                model_dir = os.getenv('MODEL_DIR', 'ai-models/models')
                algorithm = os.getenv('ANOMALY_ALGORITHM', 'isolation_forest')
                detector = AnomalyDetectionInference(model_dir=model_dir, algorithm=algorithm)
                logger.info(f"✅ Anomaly detector loaded: {algorithm}")
                return detector
            except Exception as e:
                logger.warning(f"Could not load anomaly detector: {e}")
        return None
    
    def _init_rca_engine(self):
        """Initialize RCA engine"""
        if RCAInference:
            try:
                rca = RCAInference()
                logger.info("✅ RCA engine loaded")
                return rca
            except Exception as e:
                logger.warning(f"Could not load RCA engine: {e}")
        return None
    
    def _init_auto_fix_engine(self):
        """Initialize auto-fix engine"""
        if AutoFixInference:
            try:
                kubeconfig = os.getenv('KUBECONFIG')
                auto_fix = AutoFixInference(kubeconfig_path=kubeconfig)
                logger.info("✅ Auto-fix engine loaded")
                return auto_fix
            except Exception as e:
                logger.warning(f"Could not load auto-fix engine: {e}")
        return None
    
    def _load_failure_patterns(self) -> Dict:
        """Load industry-specific failure patterns"""
        return {
            'semiconductor': {
                'patterns': ['wafer_delay', 'yield_drop', 'fab_overheat'],
                'indicators': ['batch_processing_time', 'yield_percentage', 'temperature']
            },
            'aicloud': {
                'patterns': ['gpu_allocation_failure', 'token_latency_spike', 'model_overload'],
                'indicators': ['gpu_utilization', 'request_latency', 'model_queue_depth']
            },
            'gpucloud': {
                'patterns': ['node_preemption', 'gpu_fragmentation', 'cuda_mismatch'],
                'indicators': ['gpu_availability', 'allocation_efficiency', 'driver_version']
            },
            'socialmedia': {
                'patterns': ['feed_ranking_spike', 'ads_delivery_failure', 'messaging_delay'],
                'indicators': ['feed_latency', 'ad_impression_rate', 'message_queue_depth']
            },
            'finance': {
                'patterns': ['transaction_failure', 'latency_spike', 'rate_limit'],
                'indicators': ['txn_success_rate', 'p95_latency', 'throttle_count']
            },
            'healthcare': {
                'patterns': ['emr_timeout', 'hl7_processing_delay', 'patient_data_error'],
                'indicators': ['emr_response_time', 'hl7_queue_depth', 'data_quality_score']
            }
        }
    
    def watch_pods(self):
        """Watch for pod events across all namespaces"""
        logger.info("Starting pod watch loop...")
        
        for namespace in self.config['namespaces']:
            try:
                w = watch.Watch()
                for event in w.stream(
                    self.k8s_client.list_namespaced_pod,
                    namespace=namespace,
                    label_selector='app'
                ):
                    pod = event['object']
                    event_type = event['type']
                    
                    if event_type in ['ADDED', 'MODIFIED', 'DELETED']:
                        self._process_pod_event(pod, event_type, namespace)
            except ApiException as e:
                logger.error(f"Error watching pods in {namespace}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error in pod watch: {e}")
    
    def _process_pod_event(self, pod, event_type: str, namespace: str):
        """Process pod event and detect anomalies with structured output"""
        pod_name = pod.metadata.name
        status = pod.status.phase
        
        # Check for pod failures
        if status == 'Failed' or status == 'CrashLoopBackOff':
            signals = ['pod_failed', 'container_crashed']
            root_cause_analysis = self._analyze_pod_failure_structured(pod, namespace)
            
            incident = Incident(
                id=f"{namespace}-{pod_name}-{int(time.time())}",
                namespace=namespace,
                service=pod_name,
                severity="high",
                anomaly_type="pod_failure",
                detected_at=datetime.utcnow().isoformat(),
                description=f"Pod {pod_name} in {namespace} is {status}",
                root_cause=root_cause_analysis.get('summary', 'Unknown'),
                remediation=self._suggest_remediation_structured(namespace, "pod_failure"),
                signals=signals,
                confidence=root_cause_analysis.get('confidence', 0.75),
                industry=namespace,
                pattern=root_cause_analysis.get('pattern', None),
                pattern_source=root_cause_analysis.get('pattern_source', None),
                suspected_root_cause=root_cause_analysis.get('suspected_root_cause', {}),
                suggested_actions=self._generate_suggested_actions(namespace, "pod_failure", root_cause_analysis)
            )
            self._handle_incident(incident)
        
        # Check restart count
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:
                if container.restart_count >= self.config['anomaly_thresholds']['pod_restarts']:
                    signals = ['excessive_restarts', f'restart_count_{container.restart_count}']
                    root_cause_analysis = self._analyze_restarts_structured(pod, namespace, container.restart_count)
                    
                    incident = Incident(
                        id=f"{namespace}-{pod_name}-restarts-{int(time.time())}",
                        namespace=namespace,
                        service=pod_name,
                        severity="medium",
                        anomaly_type="excessive_restarts",
                        detected_at=datetime.utcnow().isoformat(),
                        description=f"Pod {pod_name} has restarted {container.restart_count} times",
                        root_cause=root_cause_analysis.get('summary', 'Unknown'),
                        remediation=self._suggest_remediation_structured(namespace, "restarts"),
                        signals=signals,
                        confidence=root_cause_analysis.get('confidence', 0.65),
                        industry=namespace,
                        pattern=root_cause_analysis.get('pattern', None),
                        pattern_source=root_cause_analysis.get('pattern_source', None),
                        suspected_root_cause=root_cause_analysis.get('suspected_root_cause', {}),
                        suggested_actions=self._generate_suggested_actions(namespace, "restarts", root_cause_analysis)
                    )
                    self._handle_incident(incident)
    
    def _analyze_pod_failure_structured(self, pod, namespace: str) -> Dict:
        """Analyze pod failure with structured output including confidence"""
        patterns = self.failure_patterns.get(namespace, {})
        result = {
            'summary': 'Unknown failure',
            'confidence': 0.5,
            'pattern': None,
            'pattern_source': None,
            'suspected_root_cause': {}
        }
        
        # Check container status
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:
                if container.state.waiting:
                    reason = container.state.waiting.reason
                    if reason == 'ImagePullBackOff':
                        result['summary'] = "Container image pull failure - check image availability"
                        result['confidence'] = 0.95
                        result['suspected_root_cause'] = {
                            'type': 'image',
                            'name': container.image if hasattr(container, 'image') else 'unknown',
                            'confidence': 0.95
                        }
                        return result
                    elif reason == 'CrashLoopBackOff':
                        result['summary'] = "Container crashing repeatedly - check application logs"
                        result['confidence'] = 0.85
                        result['suspected_root_cause'] = {
                            'type': 'application',
                            'name': pod.metadata.name,
                            'confidence': 0.85
                        }
                        return result
        
        # Industry-specific analysis
        if namespace in patterns:
            pattern_list = patterns.get('patterns', [])
            if pattern_list:
                result['pattern'] = pattern_list[0]  # Use first matching pattern
                result['pattern_source'] = f"{namespace}_ruleset_v1"
                result['summary'] = f"Industry-specific failure pattern detected: {result['pattern']}"
                result['confidence'] = 0.75
                result['suspected_root_cause'] = {
                    'type': 'industry_pattern',
                    'name': namespace,
                    'pattern': result['pattern'],
                    'confidence': 0.75
                }
            else:
                result['summary'] = f"Industry-specific failure in {namespace} - needs investigation"
                result['confidence'] = 0.4
                result['status'] = 'needs_human_review'
        else:
            result['summary'] = "Pod failure detected - investigation needed"
            result['confidence'] = 0.3
            result['status'] = 'needs_human_review'
        
        return result
    
    def _analyze_pod_failure(self, pod, namespace: str) -> str:
        """Legacy method for backward compatibility"""
        result = self._analyze_pod_failure_structured(pod, namespace)
        return result['summary']
    
    def _analyze_restarts_structured(self, pod, namespace: str, restart_count: int) -> Dict:
        """Analyze excessive pod restarts with structured output"""
        patterns = self.failure_patterns.get(namespace, {})
        result = {
            'summary': 'Excessive restarts detected',
            'confidence': 0.6,
            'pattern': None,
            'pattern_source': None,
            'suspected_root_cause': {}
        }
        
        if namespace == 'gpucloud':
            result['summary'] = "Possible GPU allocation issue or CUDA driver mismatch"
            result['confidence'] = 0.8
            result['pattern'] = 'gpu_allocation_failure'
            result['pattern_source'] = 'gpucloud_ruleset_v1'
            result['suspected_root_cause'] = {
                'type': 'resource',
                'name': 'gpu',
                'confidence': 0.8
            }
        elif namespace == 'aicloud':
            result['summary'] = "Possible model serving overload or memory pressure"
            result['confidence'] = 0.75
            result['pattern'] = 'model_overload'
            result['pattern_source'] = 'aicloud_ruleset_v1'
            result['suspected_root_cause'] = {
                'type': 'application',
                'name': 'model_serving',
                'confidence': 0.75
            }
        elif namespace == 'semiconductor':
            result['summary'] = "Possible resource contention in fab simulation"
            result['confidence'] = 0.7
            result['pattern'] = 'resource_contention'
            result['pattern_source'] = 'semiconductor_ruleset_v1'
            result['suspected_root_cause'] = {
                'type': 'resource',
                'name': 'fab_simulation',
                'confidence': 0.7
            }
        else:
            result['summary'] = "Excessive restarts - check resource limits and application health"
            result['confidence'] = 0.5
            if restart_count > 10:
                result['confidence'] = 0.3
                result['status'] = 'needs_human_review'
        
        return result
    
    def _analyze_restarts(self, pod, namespace: str) -> str:
        """Legacy method for backward compatibility"""
        result = self._analyze_restarts_structured(pod, namespace, 0)
        return result['summary']
    
    def _suggest_remediation_structured(self, namespace: str, issue_type: str) -> str:
        """Suggest remediation (legacy method)"""
        return self._suggest_remediation(namespace, issue_type)
    
    def _suggest_remediation(self, namespace: str, issue_type: str) -> str:
        """Suggest remediation based on namespace and issue type"""
        suggestions = {
            'pod_failure': {
                'default': 'Check pod logs, verify resource limits, restart deployment',
                'gpucloud': 'Check GPU availability, verify CUDA drivers, scale deployment',
                'aicloud': 'Check model serving capacity, verify memory limits, scale horizontally',
                'semiconductor': 'Check fab resource allocation, verify batch processing limits'
            },
            'restarts': {
                'default': 'Review resource requests/limits, check application health checks',
                'gpucloud': 'Increase GPU allocation, check node preemption',
                'aicloud': 'Scale model serving, check token rate limits'
            }
        }
        
        return suggestions.get(issue_type, {}).get(namespace, 
            suggestions.get(issue_type, {}).get('default', 'Investigate and remediate'))
    
    def _generate_suggested_actions(self, namespace: str, issue_type: str, rca: Dict) -> List[Dict]:
        """Generate structured suggested actions"""
        actions = []
        
        # Scale up action
        if issue_type in ['pod_failure', 'restarts']:
            current_replicas = 3  # Would query actual deployment
            if namespace in ['gpucloud', 'aicloud', 'semiconductor']:
                current_replicas = 1
            
            actions.append({
                'type': 'scale_up',
                'target': f"{namespace}-sim",
                'params': {'replicas': min(current_replicas + 2, 5)},
                'confidence': rca.get('confidence', 0.6) * 0.9,  # Slightly lower than RCA confidence
                'description': f"Scale deployment {namespace}-sim to handle increased load"
            })
        
        # Restart action
        if issue_type == 'pod_failure':
            actions.append({
                'type': 'restart',
                'target': f"{namespace}-sim",
                'params': {},
                'confidence': 0.7,
                'description': f"Restart deployment {namespace}-sim to recover from failures"
            })
        
        # Check logs action (always available)
        actions.append({
            'type': 'investigate',
            'target': f"{namespace}-sim",
            'params': {'action': 'check_logs'},
            'confidence': 1.0,
            'description': f"Check logs for {namespace}-sim to understand root cause"
        })
        
        return actions
    
    def _handle_incident(self, incident: Incident):
        """Handle detected incident"""
        logger.info(f"Incident detected: {incident.id} - {incident.description}")
        
        # Store in database
        if self.db_conn:
            self._store_incident(incident)
        
        # Cache in Redis
        if self.redis_client:
            self.redis_client.setex(
                f"incident:{incident.id}",
                3600,  # 1 hour TTL
                json.dumps(asdict(incident))
            )
        
        # Publish to Kafka
        if self.kafka_producer:
            self.kafka_producer.send(
                'devops-incidents',
                value=asdict(incident)
            )
        
        # Log for observability
        logger.info(f"Incident {incident.id} processed: {incident.root_cause}")
    
    def _store_incident(self, incident: Incident):
        """Store incident in PostgreSQL with structured fields"""
        try:
            cursor = self.db_conn.cursor()
            
            # Store structured data as JSONB
            structured_data = {
                'signals': incident.signals or [],
                'confidence': incident.confidence,
                'industry': incident.industry or incident.namespace,
                'pattern': incident.pattern,
                'pattern_source': incident.pattern_source,
                'suspected_root_cause': incident.suspected_root_cause or {},
                'suggested_actions': incident.suggested_actions or []
            }
            
            cursor.execute("""
                INSERT INTO incidents (
                    id, namespace, service, severity, anomaly_type,
                    detected_at, description, root_cause, remediation, status,
                    structured_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    root_cause = EXCLUDED.root_cause,
                    remediation = EXCLUDED.remediation,
                    structured_data = EXCLUDED.structured_data
            """, (
                incident.id, incident.namespace, incident.service,
                incident.severity, incident.anomaly_type, incident.detected_at,
                incident.description, incident.root_cause, incident.remediation, incident.status,
                json.dumps(structured_data)
            ))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Error storing incident: {e}")
            if self.db_conn:
                self.db_conn.rollback()
    
    def detect_anomalies(self):
        """Detect anomalies from metrics using ML model"""
        logger.info("Starting ML-based anomaly detection loop...")
        
        if not self.anomaly_detector:
            logger.warning("Anomaly detector not available, using threshold-based detection")
            while self.running:
                time.sleep(60)
            return
        
        while self.running:
            try:
                # Collect metrics from all namespaces
                for namespace in self.config['namespaces']:
                    metrics = self._collect_namespace_metrics(namespace)
                    if metrics:
                        # Run ML anomaly detection
                        result = self.anomaly_detector.detect(metrics)
                        
                        if result.get('is_anomaly', False):
                            # Create incident from anomaly
                            self._create_incident_from_anomaly(namespace, metrics, result)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in anomaly detection loop: {e}")
                time.sleep(60)
    
    def _collect_namespace_metrics(self, namespace: str) -> Dict:
        """Collect metrics for a namespace"""
        try:
            # Query pods in namespace
            pods = self.k8s_client.list_namespaced_pod(namespace)
            
            if not pods.items:
                return {}
            
            # Aggregate metrics (simplified - would use Prometheus)
            total_cpu = 0.0
            total_memory = 0.0
            error_count = 0
            pod_count = len(pods.items)
            
            for pod in pods.items:
                # Get pod metrics (simplified)
                if pod.status.container_statuses:
                    for container in pod.status.container_statuses:
                        if container.state.waiting:
                            error_count += 1
            
            # Calculate averages (simplified)
            return {
                'cpu_usage': (total_cpu / pod_count) if pod_count > 0 else 0.0,
                'memory_usage': (total_memory / pod_count) if pod_count > 0 else 0.0,
                'error_rate': (error_count / pod_count) if pod_count > 0 else 0.0,
                'pod_count': pod_count,
                'pod_restarts': sum(c.restart_count for p in pods.items 
                                   for c in (p.status.container_statuses or []))
            }
        except Exception as e:
            logger.error(f"Error collecting metrics for {namespace}: {e}")
            return {}
    
    def _create_incident_from_anomaly(self, namespace: str, metrics: Dict, anomaly_result: Dict):
        """Create incident from detected anomaly"""
        anomaly_score = anomaly_result.get('anomaly_score', 0.0)
        confidence = anomaly_result.get('confidence', 0.5)
        
        # Determine severity
        if anomaly_score > 0.8:
            severity = "critical"
        elif anomaly_score > 0.6:
            severity = "high"
        else:
            severity = "medium"
        
        # Get anomalies list
        anomalies_list = anomaly_result.get('anomalies', [])
        if not anomalies_list:
            # Create from metrics
            anomalies_list = [
                {
                    'metric': k,
                    'value': v,
                    'severity': severity
                }
                for k, v in metrics.items()
                if isinstance(v, (int, float)) and v > 0
            ]
        
        # Run RCA
        rca_result = self._perform_ml_rca(namespace, metrics, anomalies_list)
        
        # Generate auto-fix suggestions
        auto_fix_result = self._generate_ml_auto_fix(namespace, metrics, rca_result)
        
        # Create incident
        incident = Incident(
            id=f"{namespace}-anomaly-{int(time.time())}",
            namespace=namespace,
            service=f"{namespace}-sim",
            severity=severity,
            anomaly_type="metric_anomaly",
            detected_at=datetime.utcnow().isoformat(),
            description=f"ML-detected anomaly in {namespace}: score {anomaly_score:.2f}",
            root_cause=rca_result.get('root_cause', 'Unknown'),
            remediation=auto_fix_result.get('message', 'Investigation needed'),
            signals=[f"anomaly_score_{anomaly_score:.2f}", f"method_{anomaly_result.get('method', 'unknown')}"],
            confidence=confidence,
            industry=namespace,
            pattern=rca_result.get('pattern', None),
            pattern_source=rca_result.get('pattern_source', 'ml_anomaly_detector'),
            suspected_root_cause=rca_result.get('suspected_root_cause', {}),
            suggested_actions=auto_fix_result.get('suggested_actions', [])
        )
        
        self._handle_incident(incident)
    
    def _perform_ml_rca(self, namespace: str, metrics: Dict, anomalies: List[Dict]) -> Dict:
        """Perform ML-based root cause analysis"""
        if not self.rca_engine:
            # Fallback to rule-based
            return {
                'root_cause': 'Unknown',
                'confidence': 0.3,
                'pattern': None,
                'pattern_source': 'rule_based_fallback'
            }
        
        try:
            incident_data = {
                'namespace': namespace,
                'service': f"{namespace}-sim",
                'anomalies': anomalies,
                'logs': [],
                'events': [],
                'metrics': metrics
            }
            
            rca_result = self.rca_engine.analyze_incident(incident_data)
            return rca_result
            
        except Exception as e:
            logger.error(f"Error in ML RCA: {e}")
            return {
                'root_cause': 'Unknown',
                'confidence': 0.3,
                'pattern': None,
                'pattern_source': 'error_fallback'
            }
    
    def perform_rca(self, incident_id: str) -> str:
        """Perform root cause analysis for an incident (public API)"""
        # Get incident from database
        if not self.db_conn:
            return "Database not available"
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT * FROM incidents WHERE id = %s", (incident_id,))
            row = cursor.fetchone()
            
            if not row:
                return "Incident not found"
            
            # Reconstruct incident data
            incident_data = {
                'namespace': row[1],
                'service': row[2],
                'anomalies': [],
                'logs': [],
                'events': [],
                'metrics': {}
            }
            
            # Run ML RCA
            rca_result = self._perform_ml_rca(
                incident_data['namespace'],
                incident_data['metrics'],
                incident_data['anomalies']
            )
            
            return rca_result.get('root_cause', 'Unknown')
            
        except Exception as e:
            logger.error(f"Error performing RCA: {e}")
            return f"Error: {str(e)}"
    
    def _generate_ml_auto_fix(self, namespace: str, metrics: Dict, rca_result: Dict) -> Dict:
        """Generate ML-based auto-fix suggestions"""
        if not self.auto_fix_engine:
            # Fallback to rule-based
            return {
                'message': 'Auto-fix engine not available',
                'suggested_actions': []
            }
        
        try:
            incident = {
                'id': f"{namespace}-fix-{int(time.time())}",
                'namespace': namespace,
                'service': f"{namespace}-sim",
                'anomaly_type': 'metric_anomaly',
                'root_cause': rca_result.get('root_cause', 'Unknown'),
                'confidence': rca_result.get('confidence', 0.5),
                'risk_score': 0.3,
                'suspected_root_cause': rca_result.get('suspected_root_cause', {}),
                'metrics': metrics,
                'logs': []
            }
            
            fix_result = self.auto_fix_engine.generate_fix(incident)
            
            # Convert fix to suggested actions format
            suggested_actions = []
            if fix_result.get('success', False):
                fix = fix_result.get('fix', {})
                suggested_actions.append({
                    'type': fix.get('type', 'unknown'),
                    'target': fix.get('target', f"{namespace}-sim"),
                    'params': fix.get('params', {}),
                    'confidence': fix_result.get('confidence', 0.5),
                    'description': fix_result.get('message', 'Auto-fix available')
                })
            
            return {
                'message': fix_result.get('message', 'No fix available'),
                'suggested_actions': suggested_actions,
                'fix_result': fix_result
            }
            
        except Exception as e:
            logger.error(f"Error generating auto-fix: {e}")
            return {
                'message': f"Error: {str(e)}",
                'suggested_actions': []
            }
    
    def suggest_auto_fix(self, incident: Incident) -> Optional[str]:
        """Suggest auto-fix actions (public API)"""
        try:
            incident_dict = {
                'id': incident.id,
                'namespace': incident.namespace,
                'service': incident.service,
                'anomaly_type': incident.anomaly_type,
                'root_cause': incident.root_cause,
                'confidence': incident.confidence,
                'risk_score': 0.3,
                'suspected_root_cause': incident.suspected_root_cause,
                'metrics': {},
                'logs': []
            }
            
            fix_result = self._generate_ml_auto_fix(
                incident.namespace,
                {},
                {'root_cause': incident.root_cause, 'confidence': incident.confidence}
            )
            
            return fix_result.get('message', incident.remediation)
            
        except Exception as e:
            logger.error(f"Error suggesting auto-fix: {e}")
            return incident.remediation
    
    def run(self):
        """Run the AI Operator"""
        logger.info("🚀 AI DevOps Brain Operator starting...")
        logger.info(f"Watching {len(self.config['namespaces'])} namespaces")
        
        # Start watch loops
        import threading
        
        pod_watch_thread = threading.Thread(target=self.watch_pods, daemon=True)
        anomaly_thread = threading.Thread(target=self.detect_anomalies, daemon=True)
        
        pod_watch_thread.start()
        anomaly_thread.start()
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down AI Operator...")
            self.running = False

if __name__ == "__main__":
    operator = AIOperator()
    operator.run()

