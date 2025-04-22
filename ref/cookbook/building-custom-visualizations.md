# Building Custom Visualizations

This tutorial shows how to create a custom visualization for cubestat metrics.

## Step 1: Understand the Screen rendering system

The Screen class in `cubestat/screen.py` handles the rendering of charts. It uses the curses library to draw in the terminal. Key methods:

- `render_start()`: Prepares the screen for rendering
- `render_ruler()`: Draws the ruler with metric labels
- `render_chart()`: Draws the horizon chart for a metric
- `render_done()`: Finalizes rendering

## Step 2: Create a new visualization method

Add a new method to the Screen class:

```python
def render_sparkline(self, colors, max_value, values, row):
    """Render a sparkline visualization of values.
    
    Args:
        colors: Color scheme to use
        max_value: Maximum value for scaling
        values: List of values to render
        row: Row position to render at
    """
    if not values:
        return
    
    # Calculate display width based on terminal size
    chart_width = min(len(values), self.cols)
    
    # Prepare the sparkline character set (lower to higher)
    # Using Unicode block characters for the sparkline
    spark_chars = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    
    # Render each value as a sparkline character
    for i, value in enumerate(values[-chart_width:]):
        if i >= self.cols:
            break
            
        # Scale the value to the sparkline character range
        if max_value > 0:
            norm_value = min(1.0, max(0.0, value / max_value))
            char_index = min(len(spark_chars) - 1, 
                             int(norm_value * (len(spark_chars) - 1)))
            char = spark_chars[char_index]
        else:
            char = spark_chars[0]
        
        # Choose color based on value intensity
        color_idx = min(len(colors) - 1, 
                        int(norm_value * len(colors)))
        color = colors[color_idx]
        
        # Set color and draw the character
        self.stdscr.attron(curses.color_pair(color))
        self.stdscr.addstr(row, i, char)
        self.stdscr.attroff(curses.color_pair(color))
```

## Step 3: Update Cubestat to use the new visualization

Modify the Cubestat class to support the new visualization:

```python
# Add a new mode to ViewMode
class ViewMode(DisplayMode):
    off = "off"
    one = "one"
    all = "all"
    sparkline = "sparkline"  # New visualization mode

# Update the render method to use the new visualization
def render(self) -> None:
    # ... existing code ...
    
    if self.view == ViewMode.sparkline:
        # Use sparkline visualization
        self.screen.render_sparkline(theme, max_value, data_slice, row)
    else:
        # Use horizon chart (existing)
        self.screen.render_chart(theme, max_value, data_slice, row)
    
    # ... rest of existing code ...
```

## Step 4: Add a keyboard shortcut to toggle the visualization

Update the InputHandler to support toggling the visualization:

```python
def handle_input(self):
    # ... existing code ...
    
    elif c == ord('y'):  # 'y' toggles visualization mode
        self.app.view = self.app.view.next()
        self.app.settings_changed = True
    
    # ... rest of existing code ...
```

## Step 5: Update the command-line help

Update the argparse configuration:

```python
parser.add_argument(
    '--view',
    type=ViewMode,
    default=ViewMode.one,
    choices=list(ViewMode),
    help='Display mode (off, one, all, sparkline). Hotkey: "v".'
)
```

## Step 6: Test the new visualization

Run cubestat with your new visualization mode:

```bash
pip install -e .
cubestat --view sparkline
```

Or press the 'y' key to toggle between visualization modes.

## Creating a Heatmap Visualization

Let's create another visualization type - a heatmap:

```python
def render_heatmap(self, colors, max_value, values, row):
    """Render a heatmap visualization of values.
    
    Args:
        colors: Color scheme to use
        max_value: Maximum value for scaling
        values: List of values to render
        row: Row position to render at
    """
    if not values:
        return
    
    # Calculate display width based on terminal size
    chart_width = min(len(values), self.cols)
    
    # Use a single character with different background colors
    char = ' '
    
    # Render each value as a colored block
    for i, value in enumerate(values[-chart_width:]):
        if i >= self.cols:
            break
            
        # Scale the value and choose a color
        if max_value > 0:
            norm_value = min(1.0, max(0.0, value / max_value))
            color_idx = min(len(colors) - 1, 
                           int(norm_value * len(colors)))
        else:
            color_idx = 0
            
        color = colors[color_idx]
        
        # Set background color and draw the character
        self.stdscr.attron(curses.color_pair(color))
        self.stdscr.addstr(row, i, char)
        self.stdscr.attroff(curses.color_pair(color))
```

## Creating a Text-Based Bar Chart

Another visualization option is a simple text-based bar chart:

```python
def render_barchart(self, colors, max_value, values, row):
    """Render a text-based bar chart of values.
    
    Args:
        colors: Color scheme to use
        max_value: Maximum value for scaling
        values: List of values to render
        row: Row position to render at
    """
    if not values or max_value <= 0:
        return
    
    # Limit the number of values to display
    chart_width = min(len(values), self.cols - 10)  # Leave space for value text
    
    # Get the most recent value
    latest_value = values[-1] if values else 0
    bar_length = min(int(latest_value / max_value * chart_width), chart_width)
    
    # Format the value as text
    value_text = f"{latest_value:.1f}"
    
    # Choose color based on value intensity
    norm_value = min(1.0, max(0.0, latest_value / max_value))
    color_idx = min(len(colors) - 1, int(norm_value * len(colors)))
    color = colors[color_idx]
    
    # Draw the bar
    self.stdscr.attron(curses.color_pair(color))
    for i in range(bar_length):
        self.stdscr.addstr(row, i, "█")
    self.stdscr.attroff(curses.color_pair(color))
    
    # Draw the value
    self.stdscr.addstr(row, bar_length + 1, value_text)
```

## Understanding Color in Cubestat

Cubestat uses a color theme system for visualizations. The colors are defined in `cubestat/colors.py`. Understanding this system is essential for creating good visualizations:

```python
def get_colors(max_colors):
    """Get color scheme based on terminal capabilities.
    
    Args:
        max_colors: Maximum number of colors supported
        
    Returns:
        List of color indices to use
    """
    if max_colors >= 256:
        # Use a gradient for 256-color terminals
        return [16, 22, 28, 34, 40, 46, 82, 118, 154, 190, 226, 220, 214, 208, 202, 196]
    elif max_colors >= 8:
        # Use basic colors for 8-color terminals
        return [curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_RED]
    else:
        # Monochrome fallback
        return [curses.COLOR_WHITE]
```

## Tips for Creating Visualizations

### 1. Handle different terminal sizes

Always check the terminal dimensions and adapt your visualization:

```python
def render_visualization(self, colors, max_value, values, row):
    # Get current dimensions
    max_y, max_x = self.stdscr.getmaxyx()
    
    # Adjust visualization to available space
    display_width = min(len(values), max_x - 1)
    if row >= max_y:
        return  # Don't render if outside visible area
    
    # Render visualization...
```

### 2. Support different color depths

Terminals support different numbers of colors. Handle this gracefully:

```python
def get_visualization_colors(self, theme, color_count):
    """Get appropriate colors for current terminal.
    
    Args:
        theme: Base color theme
        color_count: Number of colors to return
        
    Returns:
        List of color pairs appropriate for terminal
    """
    if curses.COLORS >= 256:
        # Full color theme
        return theme[:color_count]
    elif curses.COLORS >= 8:
        # Reduced color set
        return [curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_RED]
    else:
        # Monochrome
        return [curses.COLOR_WHITE]
```

### 3. Optimize rendering performance

Be mindful of performance, especially for rapidly updating visualizations:

```python
def render_optimized(self, colors, max_value, values, row):
    # Only redraw cells that changed
    if not hasattr(self, '_last_values'):
        self._last_values = {}
    
    for i, value in enumerate(values):
        # Skip if position is off-screen
        if i >= self.cols:
            break
            
        # Skip if value hasn't changed
        key = f"{row}_{i}"
        if key in self._last_values and self._last_values[key] == value:
            continue
            
        # Update stored value
        self._last_values[key] = value
        
        # Render only this cell
        # ... (rendering code)
```

### 4. Support both Unicode and ASCII

Not all terminals support Unicode. Provide fallbacks:

```python
def get_bar_chars(self):
    """Get bar characters based on terminal capabilities."""
    try:
        # Try to write a Unicode character
        self.stdscr.addstr(0, 0, "█")
        self.stdscr.refresh()
        # If successful, use Unicode block characters
        return [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
    except:
        # Fallback to ASCII
        return [' ', '.', ':', 'i', 'I', 'H', 'W', 'M', '#']
```

## Next Steps

- [Creating Load Generators](./creating-load-generators.md)
- [Adding Command-Line Options](./adding-command-line-options.md)
- [Custom Data Exporters](./custom-data-exporters.md)