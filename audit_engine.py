"""
ISO 27001 Annex A.8 - Audit Engine
===================================
Evaluates uploaded system configuration against defined rules.
Simple, focused engine that loads rules from YAML and evaluates
them against the collected system configuration JSON.
"""

import yaml
import json
import os
from datetime import datetime


class AuditEngine:
    """Evaluates system config against ISO 27001 A.8 rules."""

    def __init__(self, rules_path=None):
        if rules_path is None:
            rules_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'rules', 'rules.yml'
            )
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, rules_path):
        """Load rules from YAML file."""
        with open(rules_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data.get('rules', [])

    def evaluate(self, config_data):
        """
        Evaluate all rules against the provided config data.

        Args:
            config_data: dict from the uploaded system_config.json

        Returns:
            dict with summary and per-rule results
        """
        results = []
        passed = 0
        failed = 0
        errors = 0

        for rule in self.rules:
            result = self._evaluate_rule(rule, config_data)
            results.append(result)

            if result['status'] == 'PASS':
                passed += 1
            elif result['status'] == 'FAIL':
                failed += 1
            else:
                errors += 1

        total = len(results)
        compliance_pct = round((passed / total * 100), 1) if total > 0 else 0

        # Group results by control
        controls = {}
        for r in results:
            ctrl = r['control']
            if ctrl not in controls:
                controls[ctrl] = {
                    'control': ctrl,
                    'control_name': r['control_name'],
                    'checks': []
                }
            controls[ctrl]['checks'].append(r)

        return {
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'compliance_percentage': compliance_pct,
                'timestamp': datetime.now().isoformat(),
                'hostname': config_data.get('system_info', {}).get('hostname', 'Unknown'),
                'os': config_data.get('system_info', {}).get('os', 'Unknown'),
                'collection_date': config_data.get('system_info', {}).get('collection_date', 'Unknown'),
            },
            'results': results,
            'controls': list(controls.values()),
            'severity_summary': {
                'high': {
                    'passed': sum(1 for r in results if r['severity'] == 'high' and r['status'] == 'PASS'),
                    'failed': sum(1 for r in results if r['severity'] == 'high' and r['status'] == 'FAIL'),
                },
                'medium': {
                    'passed': sum(1 for r in results if r['severity'] == 'medium' and r['status'] == 'PASS'),
                    'failed': sum(1 for r in results if r['severity'] == 'medium' and r['status'] == 'FAIL'),
                },
                'low': {
                    'passed': sum(1 for r in results if r['severity'] == 'low' and r['status'] == 'PASS'),
                    'failed': sum(1 for r in results if r['severity'] == 'low' and r['status'] == 'FAIL'),
                }
            }
        }

    def _evaluate_rule(self, rule, config):
        """Evaluate a single rule against config data."""
        check = rule.get('check', {})
        field = check.get('field', '')
        operator = check.get('operator', 'equals')
        expected = check.get('expected', '')

        try:
            actual = self._get_nested_value(config, field)
            status = 'PASS' if self._apply_operator(actual, operator, expected) else 'FAIL'
        except Exception as e:
            actual = f"Error: {str(e)}"
            status = 'ERROR'

        return {
            'id': rule.get('id', ''),
            'control': rule.get('control', ''),
            'control_name': rule.get('control_name', ''),
            'title': rule.get('title', ''),
            'description': rule.get('description', ''),
            'severity': rule.get('severity', 'medium'),
            'status': status,
            'actual_value': str(actual) if actual is not None else 'Not Found',
            'expected_value': str(expected),
            'operator': operator,
            'remediation': rule.get('remediation', '').strip() if status == 'FAIL' else '',
            'field': field,
        }

    def _get_nested_value(self, data, field_path):
        """
        Navigate a nested dict using dot notation.
        e.g., 'ssh_config.PermitRootLogin' -> data['ssh_config']['PermitRootLogin']
        """
        keys = field_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
            if value is None:
                return None
        return value

    def _apply_operator(self, actual, operator, expected):
        """Apply comparison operator between actual and expected values."""

        # Handle None/missing values
        if actual is None:
            if operator == 'not_exists':
                return True
            return False

        if operator == 'equals':
            return str(actual).strip().lower() == str(expected).strip().lower()

        elif operator == 'not_equals':
            return str(actual).strip().lower() != str(expected).strip().lower()

        elif operator == 'less_than_equal':
            try:
                return float(actual) <= float(expected)
            except (ValueError, TypeError):
                return False

        elif operator == 'greater_than_equal':
            try:
                return float(actual) >= float(expected)
            except (ValueError, TypeError):
                return False

        elif operator == 'greater_than':
            try:
                return float(actual) > float(expected)
            except (ValueError, TypeError):
                return False

        elif operator == 'less_than':
            try:
                return float(actual) < float(expected)
            except (ValueError, TypeError):
                return False

        elif operator == 'contains':
            return str(expected).lower() in str(actual).lower()

        elif operator == 'not_contains':
            return str(expected).lower() not in str(actual).lower()

        elif operator == 'is_true':
            if isinstance(actual, bool):
                return actual is True
            return str(actual).strip().lower() in ('true', 'yes', '1')

        elif operator == 'is_false':
            if isinstance(actual, bool):
                return actual is False
            return str(actual).strip().lower() in ('false', 'no', '0')

        elif operator == 'exists':
            return actual is not None and str(actual).strip() != ''

        elif operator == 'not_exists':
            return actual is None or str(actual).strip() == ''

        else:
            return False
