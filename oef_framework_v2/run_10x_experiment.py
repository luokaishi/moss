"""
10倍加速实验启动脚本
"""

import sys
sys.path.append('/home/admin/.openclaw/workspace')

from oef_framework_v2.real_long_term_experiment import RealLongTermExperiment

# 10倍加速实验（5天压缩到12小时）
experiment = RealLongTermExperiment(
    experiment_name='oef_5day_fast_10x',
    duration_days=5.0,
    cycles_per_minute=10,
    save_interval_hours=0.5,
    report_interval_hours=2.0
)

print('🚀 启动10倍加速实验...')
print('预计完成时间：12小时后（明天中午12:31）')
experiment.run()