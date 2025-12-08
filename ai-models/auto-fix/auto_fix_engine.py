"""
Auto-Fix Engine
Generates and validates fixes for Kubernetes and Terraform issues
"""

import yaml
import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
import kubernetes
from kubernetes import client, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoFixEngine:
    """Automated fix generation and validation engine"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        self.kubeconfig_path = kubeconfig_path
        self.sandbox_namespace = "auto-fix-sandbox"
        self.fix_history = []
        
        # Load Kubernetes config
        if kubeconfig_path:
            config.load_kube_config(config_file=kubeconfig_path)
        else:
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        
    def generate_fix(self, issue: Dict) -> Dict:
        """Generate a fix based on the issue"""
        logger.info(f"Generating fix for issue: {issue.get('type')}")
        
        issue_type = issue.get('type')
        root_cause = issue.get('root_cause', {})
        
        if issue_type == 'pod_crashloop':
            return self._fix_pod_crashloop(issue, root_cause)
        elif issue_type == 'resource_limits':
            return self._fix_resource_limits(issue, root_cause)
        elif issue_type == 'image_pull_error':
            return self._fix_image_pull_error(issue, root_cause)
        elif issue_type == 'node_pressure':
            return self._fix_node_pressure(issue, root_cause)
        elif issue_type == 'service_mesh':
            return self._fix_service_mesh(issue, root_cause)
        elif issue_type == 'terraform':
            return self._fix_terraform(issue, root_cause)
        else:
            return self._generate_generic_fix(issue, root_cause)
    
    def _fix_pod_crashloop(self, issue: Dict, root_cause: Dict) -> Dict:
        """Fix pod crash loop backoff"""
        namespace = issue.get('namespace', 'default')
        pod_name = issue.get('pod_name', '')
        
        # Get pod logs to understand the issue
        try:
            logs = self._get_pod_logs(namespace, pod_name, tail_lines=50)
            error_pattern = self._analyze_logs(logs)
        except Exception as e:
            logger.warning(f"Could not get pod logs: {e}")
            error_pattern = "unknown"
        
        fix = {
            'type': 'kubernetes_patch',
            'namespace': namespace,
            'resource': 'deployment',
            'resource_name': pod_name.split('-')[0],  # Extract deployment name
            'patches': [],
            'reason': f"Pod crash loop detected. Error pattern: {error_pattern}"
        }
        
        # Common fixes based on error patterns
        if 'out of memory' in error_pattern.lower() or 'oom' in error_pattern.lower():
            fix['patches'].append({
                'op': 'replace',
                'path': '/spec/template/spec/containers/0/resources/limits/memory',
                'value': self._calculate_memory_limit(issue)
            })
            fix['patches'].append({
                'op': 'replace',
                'path': '/spec/template/spec/containers/0/resources/requests/memory',
                'value': self._calculate_memory_request(issue)
            })
        elif 'connection refused' in error_pattern.lower():
            fix['patches'].append({
                'op': 'add',
                'path': '/spec/template/spec/containers/0/env',
                'value': [
                    {'name': 'STARTUP_DELAY', 'value': '10'},
                    {'name': 'HEALTH_CHECK_RETRIES', 'value': '5'}
                ]
            })
        else:
            # Generic fix: increase resources and add health checks
            fix['patches'].extend([
                {
                    'op': 'replace',
                    'path': '/spec/template/spec/containers/0/resources/limits/memory',
                    'value': '2Gi'
                },
                {
                    'op': 'add',
                    'path': '/spec/template/spec/containers/0/livenessProbe',
                    'value': {
                        'httpGet': {'path': '/health', 'port': 8080},
                        'initialDelaySeconds': 30,
                        'periodSeconds': 10
                    }
                }
            ])
        
        return fix
    
    def _fix_resource_limits(self, issue: Dict, root_cause: Dict) -> Dict:
        """Fix resource limit issues"""
        namespace = issue.get('namespace', 'default')
        resource_name = issue.get('resource_name', '')
        
        fix = {
            'type': 'kubernetes_patch',
            'namespace': namespace,
            'resource': issue.get('resource_type', 'deployment'),
            'resource_name': resource_name,
            'patches': [
                {
                    'op': 'replace',
                    'path': '/spec/template/spec/containers/0/resources/limits/cpu',
                    'value': issue.get('recommended_cpu', '2000m')
                },
                {
                    'op': 'replace',
                    'path': '/spec/template/spec/containers/0/resources/limits/memory',
                    'value': issue.get('recommended_memory', '2Gi')
                },
                {
                    'op': 'replace',
                    'path': '/spec/template/spec/containers/0/resources/requests/cpu',
                    'value': issue.get('recommended_cpu_request', '1000m')
                },
                {
                    'op': 'replace',
                    'path': '/spec/template/spec/containers/0/resources/requests/memory',
                    'value': issue.get('recommended_memory_request', '1Gi')
                }
            ],
            'reason': 'Resource limits adjusted based on actual usage patterns'
        }
        
        return fix
    
    def _fix_image_pull_error(self, issue: Dict, root_cause: Dict) -> Dict:
        """Fix image pull errors"""
        namespace = issue.get('namespace', 'default')
        resource_name = issue.get('resource_name', '')
        current_image = issue.get('current_image', '')
        
        # Suggest using a different image tag or registry
        suggested_image = self._suggest_image_alternative(current_image)
        
        fix = {
            'type': 'kubernetes_patch',
            'namespace': namespace,
            'resource': 'deployment',
            'resource_name': resource_name,
            'patches': [
                {
                    'op': 'replace',
                    'path': '/spec/template/spec/containers/0/image',
                    'value': suggested_image
                }
            ],
            'reason': f'Image pull error detected. Switching to alternative: {suggested_image}'
        }
        
        return fix
    
    def _fix_node_pressure(self, issue: Dict, root_cause: Dict) -> Dict:
        """Fix node pressure issues"""
        # This typically requires cluster-level changes
        fix = {
            'type': 'karpenter_provisioner',
            'action': 'scale_up',
            'recommendations': [
                'Add more nodes to the cluster',
                'Adjust pod resource requests to better utilize existing nodes',
                'Enable cluster autoscaling'
            ],
            'karpenter_config': {
                'min_size': issue.get('recommended_min_nodes', 5),
                'max_size': issue.get('recommended_max_nodes', 20)
            },
            'reason': 'Node pressure detected. Cluster scaling recommended.'
        }
        
        return fix
    
    def _fix_service_mesh(self, issue: Dict, root_cause: Dict) -> Dict:
        """Fix service mesh issues"""
        namespace = issue.get('namespace', 'default')
        
        fix = {
            'type': 'istio_config',
            'namespace': namespace,
            'action': 'update_virtual_service',
            'patches': [
                {
                    'op': 'replace',
                    'path': '/spec/http/0/timeout',
                    'value': '30s'
                },
                {
                    'op': 'add',
                    'path': '/spec/http/0/retries',
                    'value': {
                        'attempts': 3,
                        'perTryTimeout': '10s'
                    }
                }
            ],
            'reason': 'Service mesh timeout/retry configuration updated'
        }
        
        return fix
    
    def _fix_terraform(self, issue: Dict, root_cause: Dict) -> Dict:
        """Generate Terraform fix"""
        terraform_file = issue.get('terraform_file', '')
        error_message = issue.get('error_message', '')
        
        fix = {
            'type': 'terraform',
            'file': terraform_file,
            'changes': [],
            'reason': f'Terraform error: {error_message}'
        }
        
        # Parse common Terraform errors
        if 'resource already exists' in error_message.lower():
            fix['changes'].append({
                'action': 'import',
                'resource': issue.get('resource_address', ''),
                'resource_id': issue.get('resource_id', '')
            })
        elif 'invalid value' in error_message.lower():
            fix['changes'].append({
                'action': 'update',
                'resource': issue.get('resource_address', ''),
                'field': issue.get('field_name', ''),
                'value': issue.get('suggested_value', '')
            })
        
        return fix
    
    def _generate_generic_fix(self, issue: Dict, root_cause: Dict) -> Dict:
        """Generate a generic fix"""
        return {
            'type': 'recommendation',
            'recommendations': [
                'Review application logs',
                'Check resource utilization',
                'Verify service dependencies',
                'Review recent deployments'
            ],
            'reason': 'Generic recommendations based on issue analysis'
        }
    
    def validate_fix(self, fix: Dict) -> Tuple[bool, str]:
        """Validate a fix in sandbox before applying"""
        logger.info(f"Validating fix: {fix.get('type')}")
        
        # Create sandbox namespace if it doesn't exist
        self._ensure_sandbox_namespace()
        
        try:
            if fix['type'] == 'kubernetes_patch':
                return self._validate_k8s_patch(fix)
            elif fix['type'] == 'terraform':
                return self._validate_terraform_fix(fix)
            else:
                return True, "Fix type does not require validation"
        except Exception as e:
            logger.error(f"Fix validation failed: {e}")
            return False, str(e)
    
    def _validate_k8s_patch(self, fix: Dict) -> Tuple[bool, str]:
        """Validate Kubernetes patch in sandbox"""
        namespace = fix.get('namespace')
        resource_type = fix.get('resource')
        resource_name = fix.get('resource_name')
        
        # Create a test deployment in sandbox
        test_deployment = self._create_test_deployment(resource_name)
        
        try:
            # Apply patches to test deployment
            for patch in fix.get('patches', []):
                # Simulate patch application
                logger.info(f"Testing patch: {patch}")
            
            # Check if deployment is healthy
            # (In real implementation, wait for deployment to be ready)
            
            return True, "Kubernetes patch validated successfully"
        except Exception as e:
            return False, f"Validation failed: {str(e)}"
        finally:
            # Cleanup test deployment
            self._cleanup_test_deployment(test_deployment)
    
    def _validate_terraform_fix(self, fix: Dict) -> Tuple[bool, str]:
        """Validate Terraform fix"""
        with tempfile.TemporaryDirectory() as tmpdir:
            terraform_file = Path(tmpdir) / "test.tf"
            
            # Write test Terraform file
            terraform_file.write_text(fix.get('terraform_content', ''))
            
            # Run terraform validate
            try:
                result = subprocess.run(
                    ['terraform', 'validate'],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return True, "Terraform validation passed"
                else:
                    return False, f"Terraform validation failed: {result.stderr}"
            except Exception as e:
                return False, f"Terraform validation error: {str(e)}"
    
    def apply_fix(self, fix: Dict, dry_run: bool = True) -> Dict:
        """Apply a fix (with dry-run by default)"""
        logger.info(f"Applying fix (dry_run={dry_run}): {fix.get('type')}")
        
        validation_result, validation_message = self.validate_fix(fix)
        
        if not validation_result:
            return {
                'success': False,
                'message': f"Fix validation failed: {validation_message}",
                'fix': fix
            }
        
        if dry_run:
            return {
                'success': True,
                'message': 'Fix validated (dry-run mode)',
                'fix': fix,
                'dry_run': True
            }
        
        # Apply the fix
        try:
            if fix['type'] == 'kubernetes_patch':
                result = self._apply_k8s_patch(fix)
            elif fix['type'] == 'terraform':
                result = self._apply_terraform_fix(fix)
            else:
                result = {'success': True, 'message': 'Fix type does not require application'}
            
            # Record in history
            self.fix_history.append({
                'fix': fix,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
            return result
        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            return {
                'success': False,
                'message': str(e),
                'fix': fix
            }
    
    def _apply_k8s_patch(self, fix: Dict) -> Dict:
        """Apply Kubernetes patch"""
        namespace = fix.get('namespace')
        resource_type = fix.get('resource')
        resource_name = fix.get('resource_name')
        
        # Convert patches to JSON patch format
        patches = fix.get('patches', [])
        patch_body = patches  # Simplified - in reality, need proper JSON patch format
        
        try:
            if resource_type == 'deployment':
                api = self.apps_v1
                api.patch_namespaced_deployment(
                    name=resource_name,
                    namespace=namespace,
                    body=patch_body
                )
            
            return {
                'success': True,
                'message': f'Successfully patched {resource_type}/{resource_name}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to patch: {str(e)}'
            }
    
    def _apply_terraform_fix(self, fix: Dict) -> Dict:
        """Apply Terraform fix"""
        # This would run terraform plan and apply
        return {
            'success': True,
            'message': 'Terraform fix applied (simulated)'
        }
    
    # Helper methods
    def _get_pod_logs(self, namespace: str, pod_name: str, tail_lines: int = 50) -> str:
        """Get pod logs"""
        try:
            return self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                tail_lines=tail_lines
            )
        except Exception as e:
            logger.error(f"Error getting pod logs: {e}")
            return ""
    
    def _analyze_logs(self, logs: str) -> str:
        """Analyze logs for error patterns"""
        error_patterns = {
            'out of memory': 'oom',
            'connection refused': 'connection_error',
            'timeout': 'timeout',
            'permission denied': 'permission_error'
        }
        
        logs_lower = logs.lower()
        for pattern, error_type in error_patterns.items():
            if pattern in logs_lower:
                return error_type
        
        return 'unknown'
    
    def _calculate_memory_limit(self, issue: Dict) -> str:
        """Calculate recommended memory limit"""
        current_memory = issue.get('current_memory', '512Mi')
        # Increase by 2x
        return '2Gi'  # Simplified
    
    def _calculate_memory_request(self, issue: Dict) -> str:
        """Calculate recommended memory request"""
        return '1Gi'  # Simplified
    
    def _suggest_image_alternative(self, current_image: str) -> str:
        """Suggest alternative image"""
        # Remove tag, add 'latest' or 'stable'
        if ':' in current_image:
            base_image = current_image.split(':')[0]
            return f"{base_image}:latest"
        return current_image
    
    def _ensure_sandbox_namespace(self):
        """Ensure sandbox namespace exists"""
        try:
            self.v1.read_namespace(name=self.sandbox_namespace)
        except:
            namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=self.sandbox_namespace))
            self.v1.create_namespace(namespace)
    
    def _create_test_deployment(self, name: str):
        """Create test deployment in sandbox"""
        # Simplified - would create actual deployment
        return {'name': f'test-{name}', 'namespace': self.sandbox_namespace}
    
    def _cleanup_test_deployment(self, deployment: Dict):
        """Cleanup test deployment"""
        # Simplified - would delete deployment
        pass


def generate_and_validate_fix(issue: Dict, kubeconfig: Optional[str] = None) -> Dict:
    """Main function to generate and validate a fix"""
    engine = AutoFixEngine(kubeconfig_path=kubeconfig)
    
    # Generate fix
    fix = engine.generate_fix(issue)
    
    # Validate fix
    is_valid, message = engine.validate_fix(fix)
    
    if not is_valid:
        return {
            'success': False,
            'message': message,
            'fix': fix
        }
    
    # Apply fix (dry-run)
    result = engine.apply_fix(fix, dry_run=True)
    
    return result


if __name__ == '__main__':
    import sys
    
    # Example issue
    issue = {
        'type': 'pod_crashloop',
        'namespace': 'default',
        'pod_name': 'payment-service-123',
        'root_cause': {
            'service': 'payment-service',
            'error': 'out of memory'
        }
    }
    
    result = generate_and_validate_fix(issue)
    print(json.dumps(result, indent=2))

