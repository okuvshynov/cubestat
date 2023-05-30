# Horizon charts for Apple M1/M2 monitoring

Command-line utility to monitor various resource utilization on Apple M1/M2 devices.

Usage:
```
% ./cubestat.py --help
usage: ./cubestat.py [-h] [--refresh_ms REFRESH_MS] [--buffer_size BUFFER_SIZE]

options:
  -h, --help            show this help message and exit
  --refresh_ms REFRESH_MS, -i REFRESH_MS
  --buffer_size BUFFER_SIZE
```

Needs sudo access as it calls powermetrics.

Monitors:
1. CPU utilization 
2. GPU util
3. ANE power consumption
4. disk io
5. network io


Example: running [deep RL loop](https://github.com/okuvshynov/rlscout) (self play to generate data, model training, model evaluation) on a single MacBook Air:

![Deep Rl horizon chart here](static/cubestat_rl_loop.png)

