"""
Performance Monitoring Decorator
================================

Lightweight performance monitor with timing decorator for function execution and summary generation.

Features:
- Function execution timing
- Performance statistics
- Summary report generation
- Decorator pattern
- Production-ready lightweight design
- Minimal overhead

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import time
import functools
import threading
import os
from typing import Dict, List, Any
import json


class PerformanceMonitor:

    def __init__(self):
        self.timings: Dict[str, List[float]] = {}
        self.call_counts: Dict[str, int] = {}
        self.start_time = time.time()
        self.active_calls: Dict[str, float] = {}

    def timing_decorator(self, func_name: str = None):
        """Decorator to time function execution"""

        def decorator(func):
            name = func_name or f"{func.__module__}.{func.__qualname__}"

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                self.active_calls[name] = start_time

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.time()
                    duration = end_time - start_time

                    # Record timing
                    if name not in self.timings:
                        self.timings[name] = []
                        self.call_counts[name] = 0

                    self.timings[name].append(duration)
                    self.call_counts[name] += 1

                    # Remove from active calls
                    self.active_calls.pop(name, None)

                    # Log significant delays
                    if duration > 1.0:
                        print(f"⏱️  {name}: {duration:.2f}s")

            return wrapper

        return decorator

    def get_performance_summary(self) -> str:
        """Get performance summary"""
        if not self.timings:
            return "No performance data available"

        summary = []
        summary.append("Performance Summary:")

        # Calculate total time per function
        function_totals = {}
        for func_name, times in self.timings.items():
            total = sum(times)
            avg = total / len(times)
            function_totals[func_name] = {
                'total': total,
                'average': avg,
                'calls': len(times)
            }

        # Sort by total time
        sorted_functions = sorted(function_totals.items(),
                                  key=lambda x: x[1]['total'], reverse=True)

        for func_name, stats in sorted_functions[:5]:  # Top 5
            summary.append(
                f"  {func_name}: {stats['total']:.2f}s total, {stats['average']:.3f}s avg, {stats['calls']} calls")

        return "\n".join(summary)


# Global monitor instance
monitor = PerformanceMonitor()


def profile_method(func_name: str = None):
    """Decorator for profiling methods"""
    return monitor.timing_decorator(func_name)