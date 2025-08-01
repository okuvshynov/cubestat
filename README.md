# system monitoring horizon charts for terminal

cubestat is a command-line utility to monitor system metrics in horizon chart format. It was originally created for Apple M1/M2 devices, but supports Linux with NVIDIA GPU as well, including Google Colab environment.
Numerous tools exist for tracking system metrics, yet horizon charts stand out due to their good information density which enables the display of many time-series data on a single screen.

Let's start with an example:

https://github.com/okuvshynov/cubestat/assets/661042/8e1e405e-ca61-4ffb-bedb-e04eb33f8bc2

In the clip above we see Mixtral-8x7b inference on MacBook Air with FF layers offloaded to SSD. 
We can notice somewhat low GPU util, 2Gb/s+ of data read from disk, as we have to fetch the weights, but plenty of free RAM (And we are actually able to serve almost 100Gb model on 24Gb machine with fp16 precision, even if very slow).

We can also clearly see moment of change from model loading (cpu util, disk writes for model preprocessing) to model inference (disk reads, gpu util going up, cpu going down)

Currently cubestat reports:
1. CPU utilization - configurable per core ('by_core'), cluster of cores on Apple M1+: Efficiency/Performance ('by_cluster') or all. Is shown as percentage.
2. GPU utilization per card/chip. Is shown in percentage. Works for Apple's M1/M2 SoC and NVIDIA GPUs. For NVIDIA GPU can show VRAM usage as well. In case of multi-GPU can show individual GPUs or aggregated average.
3. ANE (Neural Engine) power consumption. According to `man powermetrics` it is an estimate, but seems working good enough as a proxy to ANE utilization. Is shown as percentage.
4. Disk and network IO; Is shown as rate (KB/s, MB/s, GB/s).
5. Memory usage in %
6. Swap usage. Is shown as absolute value (KB, MB, GB)

Known limitations:
1. **On MacOS cubestat needs to run `powermetrics` with sudo**. You don't need to run cubestat itself with sudo, but you'll be asked sudo password when cubestat launches powermetrics. If you are comfortable doing that, you can add `powermetrics` to `/etc/sudoers` (`your_user_name ALL=(ALL) NOPASSWD: /usr/bin/powermetrics`) and avoid this.
2. Neural engine utilization is an estimate based on power usage, more on that below.
3. Needs 256 colors terminal

## Installation:

```
% pip install cubestat
```

or 

```
% pip install cubestat[cuda] # for instances with NVIDIA
```

## Usage

```
usage: cubestat [-h] [--refresh_ms REFRESH_MS] [--buffer_size BUFFER_SIZE] [--view {off,one,all}] [--csv] [--cpu {all,by_cluster,by_core}] [--gpu {collapsed,load_only,load_and_vram}] [--swap {show,hide}] [--network {show,hide}] [--disk {show,hide}]
                [--power {combined,all,off}]

options:
  -h, --help            show this help message and exit
  --refresh_ms REFRESH_MS, -i REFRESH_MS
                        Update frequency, milliseconds
  --buffer_size BUFFER_SIZE
                        How many datapoints to store. Having it larger than screen width is a good idea as terminal window can be resized
  --view {off,one,all}  legend/values/time mode. Can be toggled by pressing v.
  --csv                 Export metrics in CSV format to stdout (bypasses TUI)
  --cpu {all,by_cluster,by_core}
                        CPU mode - showing all cores, only cumulative by cluster or both. Can be toggled by pressing c.
  --gpu {collapsed,load_only,load_and_vram}
                        GPU mode - hidden, showing all GPUs load, or showing load and vram usage. Can be toggled by pressing g.
  --swap {show,hide}    Show swap . Can be toggled by pressing s.
  --network {show,hide}
                        Show network io. Can be toggled by pressing n.
  --disk {show,hide}    Show disk read/write. Can be toggled by pressing d.
  --power {combined,all,off}
                        Power mode - off, showing breakdown CPU/GPU/ANE load, or showing combined usage. Can be toggled by pressing p.
```

Interactive commands:
* q - quit
* v - toggle view mode
* c - change cpu display mode (individual cores, aggregated or both)
* g - change gpu display mode (individual gpus, aggregated and optionally VRAM usage)
* d - show/hide disk reads/writes
* n - show/hide network utilization
* s - show/hide swap
* p - show/hide power usage if available
* UP/DOWN - scroll the lines in case there are more cores;
* LEFT/RIGHT - scroll left/right. Autorefresh is paused when user scrolled to non-latest position. To resume autorefresh either scroll back to the right or press '0';
* 0 - reset horizontal scroll, continue autorefresh.

## CSV Export Mode

cubestat supports CSV export for integration with monitoring systems, scripts, and data analysis tools:

```bash
# Basic CSV export
cubestat --csv

# Save to file
cubestat --csv > system_metrics.csv

# Custom refresh rate
cubestat --csv --refresh_ms 500

# Pipe to monitoring system
cubestat --csv | monitoring_ingester
```

### CSV Output Format

The CSV output uses standardized, hierarchical metric names that are self-documenting:

```csv
timestamp,metric,value
1750693377.593887,cpu.performance.0.core.0.utilization.percent,26.7591
1750693377.593887,cpu.efficiency.0.core.4.utilization.percent,12.3456
1750693377.593887,memory.system.total.used.percent,78.5
1750693377.593887,gpu.apple.0.utilization.percent,45.2
1750693377.593887,power.component.cpu.consumption.watts,2.34
1750693377.593887,network.total.rx.bytes_per_sec,1048576
1750693377.593887,disk.total.write.bytes_per_sec,2097152
```

### Integration Examples

**InfluxDB:**
```bash
cubestat --csv | while IFS=, read timestamp metric value; do
  curl -X POST "http://localhost:8086/write?db=system" \
    --data-binary "$metric value=$value $timestamp"
done
```

**Prometheus Pushgateway:**
```bash
cubestat --csv | awk -F, '
NR>1 { gsub(/\./, "_", $2); print $2" "$3 }' | \
curl --data-binary @- http://localhost:9091/metrics/job/cubestat
```

**Simple Analysis:**
```bash
# Get average CPU utilization
cubestat --csv | grep "cpu.*utilization" | awk -F, '{sum+=$3; count++} END {print sum/count}'

# Monitor memory usage
cubestat --csv | grep "memory.system.total.used.percent" | tail -f
```

## Notes and examples

### Multi-gpu example 

https://github.com/okuvshynov/cubestat/assets/661042/c5e0750d-9bbd-4636-a1ea-71cc75ebbadb

We see a workload with uneven distribution between 4 GPUs installed. By pressing 'g' we can toggle the view mode to either show aggregate load, per GPU load or per GPU load and VRAM usage.

### Apple Neural Engine utilization

A few notes on 'what does this even represent?'. Utilization we show is essentially current power consumption reported by powermetrics. To convert it to % we divide it by some maximum value observed in experimentation. When reading this metric, be aware:
* The concept of 'utilization' overall it pretty ambiguous, e.g. when CPU is wasting cycles on a cache miss, is it 'utilized' or not? If CPU is doing scalar instructions on 1 execution port rather than vectorized instructions on several ports, is it 'utilized' or not?
* It is unclear if power consumption is a decent proxy for utilization;
* The upper bound must be different for different models (M1, M1 Max, M2, etc.). I tested it on M1, M2 and M1 Pro only;
* It is unclear if my tests are actually hitting upperbound. The highest I could achieve was [multiple layers of convolutions with no non-linearities between them](scripts/apple_loadgen.py#L26-L31);

### Running on Google Colab 

We can run cubestat on Google Colab instances to monitor GPU/CPU/IO usage.

First cell:
```
!pip install cubestat[cuda]
!pip install colab-xterm
%load_ext colabxterm
# export TERM=xterm-256color <---- RUN THIS IN TERMINAL
# cubestat                   <---- RUN THIS IN TERMINAL
```

Start xterm:
```
%xterm
```

In the terminal, configure 256 colors and start cubestat:
```
# export TERM=xterm-256color
# cubestat
```

Example notebook: [colab example](https://colab.research.google.com/drive/1EUOXGJ-WUYfrKjy0oC_H2ZkVRgiSWGcC#scrollTo=0sm8bcE1QgbW)

![colab cubestat](static/colab_cubestat.png)

## Dependencies
* Python 3.8+
* psutil 5.9.5+
* [optional] pynvml for NVIDIA cards monitoring

## Development

### Installation for Development

```bash
# Clone the repository
git clone https://github.com/okuvshynov/cubestat.git
cd cubestat

# Install in development mode
pip install -e .
# Or with NVIDIA GPU support
pip install -e .[cuda]

# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
python -m unittest discover

# Run a specific test
python -m unittest cubestat.tests.test_data_manager
```

### Checking Types

```bash
# Run mypy for type checking
mypy cubestat
```

### Linting

```bash
# Run ruff for linting
ruff check cubestat
```

## TODO

- [ ] add 'help' for each metric
- [x] type hints (in progress)
- [x] better error handling and logging (in progress)
- [ ] unit tests
- [x] memory modes - more details (cache/etc), absolute values rather than %, mmap handling
- [ ] optional joint scale within metric group
- [ ] nvidia GPU - probing vs momentary load to avoid missing spikes
- [ ] support AMD GPUs
- [ ] rent on vast.ai
- [ ] support remote monitoring
- [ ] NUMA grouping
- [ ] per interface network utilization
- [ ] perf on weak machine (e.g. pi zero)
