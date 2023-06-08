# Horizon charts for Apple M1/M2 monitoring

Command-line utility to monitor CPU/GPU/NeuralEngine utilization on Apple M1/M2 devices. Requires sudo access as it calls `powermetrics` and parses its output.
Is useful when connecting to another OS X device remotely over ssh. 

```
usage: ./cubestat.py [-h]
                     [--refresh_ms REFRESH_MS]
                     [--buffer_size BUFFER_SIZE]
                     [--cpu {all,by_cluster,by_core}]
                     [--color {red,green,blue,mixed}]
                     [--percentages {hidden,last}]
                     [--disk] [--network]

options:
  -h, --help            show this help message and
                        exit
  --refresh_ms REFRESH_MS, -i REFRESH_MS
                        Update frequency,
                        milliseconds
  --buffer_size BUFFER_SIZE
                        How many datapoints to
                        store. Having it larger
                        than screen width is a
                        good idea as terminal
                        window can be resized
  --cpu {all,by_cluster,by_core}
                        CPU mode - showing all
                        cores, only cumulative by
                        cluster or both. Can be
                        toggled by pressing c.
  --color {red,green,blue,mixed}
  --percentages {hidden,last}
                        Show/hide numeric
                        utilization percentage.
                        Can be toggled by pressing
                        p.
  --disk                show disk read/write. Can
                        be toggled by pressing d.
  --network             show network io. Can be
                        toggled by pressing n.
```

Monitors:
1. CPU utilization - configurable per core ('expanded'), cluster of cores: Efficiency/Performance ('cluster') or both. Is shown as percentage.
2. GPU utilization. Is shown in percentage.
3. ANE power consumption. According to `man powermetrics` it is an estimate, but seems working good enough as a proxy to ANE utilization. Is shown as percentage.
4. Disk and network IO; Is shown in Kb/s.

We could add more data from powermetrics (e.g. frequency), but it was adding too much visual noise.

Example: running [deep RL loop](https://github.com/okuvshynov/rlscout) (self play to generate data, model training, model evaluation) on a single MacBook Air M2:

First chart we have playing games to generate data on CPU only (as there's no trained model yet).
![Self-play RL horizon chart here](static/selfplay_only.png)

Once we have enough data, we start training the model (on GPU):
![Self-play + training](static/started_training.png)

After we have first model snapshot, we start model evaluation, which runs model inference (on Neural Engine):
![Self-play + training + eval](static/started_model_eval.png)

