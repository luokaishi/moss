"""
MOSS Safety Mechanism Quantification Tests

Quantitative evaluation of the 5-level gradient safety mechanism.
Tests trigger rates, false positives, and recovery times under various scenarios.

Author: MOSS Project Team
Version: 2.0.0
"""

import sys
import json
import random
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

sys.path.insert(0, '/workspace/projects/moss')
from core.gradient_safety_guard import GradientSafetyGuard, SafetyLevel


@dataclass
class SafetyTestResult:
    """Result of a single safety test scenario."""
    scenario_name: str
    duration_minutes: int
    total_checks: int
    level_triggers: Dict[str, int]
    trigger_rate: float
    avg_recovery_time: float  # minutes
    false_positive_rate: float
    escalation_count: int


@dataclass
class SafetyQuantificationReport:
    """Complete safety quantification report."""
    timestamp: str
    test_duration_total: float  # minutes
    scenarios_tested: int
    threshold_definitions: Dict
    results: List[SafetyTestResult]
    summary: Dict


class SafetyQuantificationTester:
    """
    Quantitative testing framework for MOSS safety mechanism.
    
    Evaluates:
    - Trigger rates at each level
    - False positive/negative rates
    - Recovery time distributions
    - Escalation patterns
    """
    
    def __init__(self):
        self.guard = GradientSafetyGuard()
        self.results: List[SafetyTestResult] = []
        
        # Define thresholds for documentation
        self.thresholds = {
            'cpu': {
                'warning': 70.0,
                'throttling': 80.0,
                'pause': 90.0,
                'terminate': 95.0
            },
            'memory': {
                'warning': 60.0,
                'throttling': 70.0,
                'pause': 85.0,
                'terminate': 95.0
            },
            'error_rate': {
                'warning': 0.05,
                'throttling': 0.10,
                'pause': 0.20,
                'terminate': 0.50
            },
            'consecutive_failures': {
                'warning': 3,
                'throttling': 5,
                'pause': 10,
                'terminate': 20
            }
        }
        
        # Time between metric checks (simulated)
        self.check_interval = 5  # minutes
    
    def run_all_tests(self) -> SafetyQuantificationReport:
        """Run complete safety quantification test suite."""
        print("MOSS Safety Mechanism Quantification Tests")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Test scenarios
        scenarios = [
            ('Normal Operation', self._generate_normal_metrics, 60),
            ('Warning Boundary', self._generate_warning_metrics, 30),
            ('Throttling Boundary', self._generate_throttling_metrics, 30),
            ('Pause Boundary', self._generate_pause_metrics, 20),
            ('Recovery Pattern', self._generate_recovery_metrics, 40),
            ('Oscillating Stress', self._generate_oscillating_metrics, 45),
            ('Adversarial', self._generate_adversarial_metrics, 30),
        ]
        
        for name, metric_generator, duration in scenarios:
            result = self._test_scenario(name, metric_generator, duration)
            self.results.append(result)
            self._print_result(result)
        
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds() / 60
        
        # Generate summary
        summary = self._generate_summary()
        
        report = SafetyQuantificationReport(
            timestamp=datetime.now().isoformat(),
            test_duration_total=total_duration,
            scenarios_tested=len(scenarios),
            threshold_definitions=self.thresholds,
            results=self.results,
            summary=summary
        )
        
        return report
    
    def _test_scenario(self, name: str, metric_generator, duration_minutes: int) -> SafetyTestResult:
        """Test a specific scenario."""
        # Reset guard for clean test
        self.guard = GradientSafetyGuard()
        
        num_checks = duration_minutes // self.check_interval
        level_triggers = {level.name: 0 for level in SafetyLevel}
        escalation_count = 0
        prev_level = SafetyLevel.NORMAL
        
        recovery_times = []
        level_entry_time = None
        terminated = False
        
        for i in range(num_checks):
            # Generate metrics for this check
            metrics = metric_generator(i, num_checks)
            
            # Check safety (catch SystemExit from TERMINATE)
            try:
                level = self.guard.check_metrics(metrics)
            except SystemExit:
                # TERMINATE was triggered - record and stop this scenario
                level = SafetyLevel.TERMINATE
                level_triggers[level.name] += 1
                escalation_count += 1
                terminated = True
                break
            
            level_triggers[level.name] += 1
            
            # Track escalations
            if level.value > prev_level.value:
                escalation_count += 1
            
            # Track recovery times (returning to NORMAL from higher level)
            if level == SafetyLevel.NORMAL and prev_level != SafetyLevel.NORMAL:
                if level_entry_time:
                    recovery_time = (i - level_entry_time) * self.check_interval
                    recovery_times.append(recovery_time)
            elif level != SafetyLevel.NORMAL and prev_level == SafetyLevel.NORMAL:
                level_entry_time = i
            
            prev_level = level
        
        # Adjust total checks if terminated early
        actual_checks = i + 1 if terminated else num_checks
        
        # Calculate metrics
        non_normal_triggers = sum(level_triggers[l.name] for l in SafetyLevel if l != SafetyLevel.NORMAL)
        trigger_rate = non_normal_triggers / actual_checks if actual_checks > 0 else 0
        
        avg_recovery = np.mean(recovery_times) if recovery_times else 0
        
        # Estimate false positive rate (in normal scenarios, triggers are false positives)
        false_positive_rate = trigger_rate if 'Normal' in name else 0.0
        
        return SafetyTestResult(
            scenario_name=name,
            duration_minutes=duration_minutes,
            total_checks=actual_checks,
            level_triggers=level_triggers,
            trigger_rate=trigger_rate,
            avg_recovery_time=avg_recovery,
            false_positive_rate=false_positive_rate,
            escalation_count=escalation_count
        )
    
    def _generate_normal_metrics(self, step: int, total: int) -> Dict:
        """Generate normal operation metrics."""
        return {
            'cpu_percent': random.uniform(30, 60),
            'memory_percent': random.uniform(30, 50),
            'error_rate': random.uniform(0.001, 0.03),
            'consecutive_failures': 0
        }
    
    def _generate_warning_metrics(self, step: int, total: int) -> Dict:
        """Generate metrics at warning boundary."""
        # Oscillate around warning threshold
        phase = np.sin(step * 0.3)
        return {
            'cpu_percent': 70 + phase * 5 + random.uniform(-2, 2),
            'memory_percent': 60 + phase * 5 + random.uniform(-2, 2),
            'error_rate': 0.05 + phase * 0.01 + random.uniform(-0.005, 0.005),
            'consecutive_failures': random.randint(2, 4)
        }
    
    def _generate_throttling_metrics(self, step: int, total: int) -> Dict:
        """Generate metrics at throttling boundary."""
        phase = np.sin(step * 0.25)
        return {
            'cpu_percent': 85 + phase * 3 + random.uniform(-2, 2),
            'memory_percent': 75 + phase * 3 + random.uniform(-2, 2),
            'error_rate': 0.12 + phase * 0.02 + random.uniform(-0.01, 0.01),
            'consecutive_failures': random.randint(4, 6)
        }
    
    def _generate_pause_metrics(self, step: int, total: int) -> Dict:
        """Generate metrics at pause boundary."""
        phase = np.sin(step * 0.2)
        return {
            'cpu_percent': 92 + phase * 3 + random.uniform(-1, 1),
            'memory_percent': 88 + phase * 3 + random.uniform(-1, 1),
            'error_rate': 0.25 + phase * 0.03 + random.uniform(-0.02, 0.02),
            'consecutive_failures': random.randint(8, 12)
        }
    
    def _generate_recovery_metrics(self, step: int, total: int) -> Dict:
        """Generate metrics showing recovery pattern."""
        # Start high, gradually recover
        progress = step / total
        stress_level = max(0, 1 - progress * 1.5)  # Decreasing stress
        
        return {
            'cpu_percent': 50 + stress_level * 45 + random.uniform(-3, 3),
            'memory_percent': 45 + stress_level * 45 + random.uniform(-3, 3),
            'error_rate': 0.02 + stress_level * 0.15 + random.uniform(-0.01, 0.01),
            'consecutive_failures': int(stress_level * 10)
        }
    
    def _generate_oscillating_metrics(self, step: int, total: int) -> Dict:
        """Generate oscillating stress metrics."""
        # Multiple sine waves creating complex patterns
        osc1 = np.sin(step * 0.4)
        osc2 = np.sin(step * 0.15)
        
        return {
            'cpu_percent': 60 + osc1 * 25 + osc2 * 10 + random.uniform(-3, 3),
            'memory_percent': 55 + osc1 * 20 + osc2 * 8 + random.uniform(-3, 3),
            'error_rate': 0.08 + osc1 * 0.08 + random.uniform(-0.02, 0.02),
            'consecutive_failures': int(3 + osc1 * 3 + random.uniform(0, 2))
        }
    
    def _generate_adversarial_metrics(self, step: int, total: int) -> Dict:
        """Generate adversarial/edge case metrics."""
        # Sudden spikes
        if random.random() < 0.2:  # 20% chance of spike
            return {
                'cpu_percent': random.uniform(90, 99),
                'memory_percent': random.uniform(85, 98),
                'error_rate': random.uniform(0.3, 0.6),
                'consecutive_failures': random.randint(10, 25)
            }
        else:
            return {
                'cpu_percent': random.uniform(40, 70),
                'memory_percent': random.uniform(35, 60),
                'error_rate': random.uniform(0.01, 0.08),
                'consecutive_failures': random.randint(0, 3)
            }
    
    def _print_result(self, result: SafetyTestResult):
        """Print test result."""
        print(f"\n{result.scenario_name}:")
        print(f"  Duration: {result.duration_minutes}min, Checks: {result.total_checks}")
        print(f"  Trigger Rate: {result.trigger_rate:.2%}")
        print(f"  Level Distribution: ", end="")
        for level, count in result.level_triggers.items():
            if count > 0:
                pct = count / result.total_checks * 100
                print(f"{level}={count}({pct:.0f}%) ", end="")
        print()
        print(f"  Avg Recovery Time: {result.avg_recovery_time:.1f}min")
        print(f"  Escalations: {result.escalation_count}")
        if result.false_positive_rate > 0:
            print(f"  False Positive Rate: {result.false_positive_rate:.2%}")
    
    def _generate_summary(self) -> Dict:
        """Generate summary statistics."""
        all_trigger_rates = [r.trigger_rate for r in self.results]
        all_recovery_times = [r.avg_recovery_time for r in self.results if r.avg_recovery_time > 0]
        all_escalations = [r.escalation_count for r in self.results]
        
        # Calculate level trigger distribution across all tests
        total_triggers = {level.name: 0 for level in SafetyLevel}
        for result in self.results:
            for level, count in result.level_triggers.items():
                total_triggers[level] += count
        
        total_checks = sum(r.total_checks for r in self.results)
        
        return {
            'overall_trigger_rate': np.mean(all_trigger_rates),
            'trigger_rate_std': np.std(all_trigger_rates),
            'avg_recovery_time': np.mean(all_recovery_times) if all_recovery_times else 0,
            'recovery_time_std': np.std(all_recovery_times) if all_recovery_times else 0,
            'total_escalations': sum(all_escalations),
            'level_distribution': {
                level: {
                    'count': count,
                    'percentage': count / total_checks * 100 if total_checks > 0 else 0
                }
                for level, count in total_triggers.items()
            },
            'false_positive_scenarios': [
                r.scenario_name for r in self.results if r.false_positive_rate > 0
            ]
        }
    
    def save_report(self, report: SafetyQuantificationReport, filename: str = None):
        """Save report to JSON file."""
        if filename is None:
            filename = f"safety_quantification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert dataclasses to dicts
        report_dict = {
            'timestamp': report.timestamp,
            'test_duration_total': report.test_duration_total,
            'scenarios_tested': report.scenarios_tested,
            'threshold_definitions': report.threshold_definitions,
            'results': [asdict(r) for r in report.results],
            'summary': report.summary
        }
        
        with open(filename, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        print(f"\nReport saved to: {filename}")
        return filename


def print_threshold_table():
    """Print threshold definition table."""
    print("\n" + "=" * 60)
    print("5-Level Safety Mechanism Thresholds")
    print("=" * 60)
    
    thresholds = {
        'Metric': ['CPU %', 'Memory %', 'Error Rate', 'Consecutive Failures'],
        'Level 1\n(WARNING)': ['70%', '60%', '5%', '3'],
        'Level 2\n(THROTTLING)': ['80%', '70%', '10%', '5'],
        'Level 3\n(PAUSE)': ['90%', '85%', '20%', '10'],
        'Level 4\n(ROLLBACK)': ['95%', '95%', '50%', '20'],
        'Level 5\n(TERMINATE)': ['95%+', '95%+', '50%+', '20+']
    }
    
    # Print simple table
    print(f"{'Metric':<25} {'L1':<12} {'L2':<12} {'L3':<12} {'L4':<12} {'L5':<12}")
    print("-" * 85)
    print(f"{'CPU Usage':<25} {'>70%':<12} {'>80%':<12} {'>90%':<12} {'>95%':<12} {'>95%':<12}")
    print(f"{'Memory Usage':<25} {'>60%':<12} {'>70%':<12} {'>85%':<12} {'>95%':<12} {'>95%':<12}")
    print(f"{'Error Rate':<25} {'>5%':<12} {'>10%':<12} {'>20%':<12} {'>50%':<12} {'>50%':<12}")
    print(f"{'Consecutive Failures':<25} {'>3':<12} {'>5':<12} {'>10':<12} {'>20':<12} {'>20':<12}")
    
    print("\nActions:")
    print("  L1 (WARNING):    Log warning, notify operator")
    print("  L2 (THROTTLING): Reduce action rate by 50%")
    print("  L3 (PAUSE):      Pause all actions, manual review required")
    print("  L4 (ROLLBACK):   Rollback to last checkpoint")
    print("  L5 (TERMINATE):  Emergency termination")


if __name__ == '__main__':
    print_threshold_table()
    
    # Run tests
    tester = SafetyQuantificationTester()
    report = tester.run_all_tests()
    
    # Save report
    filename = tester.save_report(report)
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Overall Trigger Rate: {report.summary['overall_trigger_rate']:.2%}")
    print(f"Average Recovery Time: {report.summary['avg_recovery_time']:.1f}min")
    print(f"Total Escalations: {report.summary['total_escalations']}")
    print(f"\nLevel Distribution:")
    for level, data in report.summary['level_distribution'].items():
        if data['count'] > 0:
            print(f"  {level}: {data['count']} ({data['percentage']:.1f}%)")
