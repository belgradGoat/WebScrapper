# Tab Management Feature

## Overview
The NC Tool Analyzer now supports tab rearrangement and customization with persistent settings across sessions.

## Features

### Right-Click Context Menu
- **Right-click on any tab** to open the context menu with the following options:

#### Tab Movement
- **Move Left** - Move the tab one position to the left
- **Move Right** - Move the tab one position to the right  
- **Move to First** - Move the tab to the first position
- **Move to Last** - Move the tab to the last position

#### Tab Visibility
- **Hide Tab** - Hide the current tab from view
- **Show Hidden Tab** - Submenu showing all hidden tabs that can be restored

#### Reset Options
- **Reset to Default Order** - Restore original tab order and show all hidden tabs

## Persistence
- All tab arrangements are **automatically saved** to `config.json`
- Settings are **restored on application restart**
- Configuration is stored in the `ui` section:
  ```json
  {
    "ui": {
      "tab_order": ["analysis_tab_module", "results_tab_module", "machine_tab_module", "scheduler_tab_module"],
      "hidden_tabs": []
    }
  }
  ```

## Usage Examples

### Rearranging Tabs
1. Right-click on the "Results" tab
2. Select "Move to First" to make it the leftmost tab
3. The change is immediately applied and saved

### Hiding Tabs  
1. Right-click on a tab you don't frequently use
2. Select "Hide Tab"
3. The tab disappears and the layout adjusts

### Restoring Hidden Tabs
1. Right-click on any visible tab
2. Hover over "Show Hidden Tab"
3. Select the tab you want to restore from the submenu

### Resetting Layout
1. Right-click on any tab
2. Select "Reset to Default Order"
3. All tabs return to original positions and all hidden tabs become visible

## Technical Details

### Default Tab Order
The default tab order is determined by the module loading sequence:
1. Analysis Tab (🔍)
2. Machine Management Tab (🏭)  
3. Results Tab (📊)
4. Scheduler Tab (📅)

### Configuration Storage
- Tab order stored as array of module names
- Hidden tabs stored as separate array
- Changes saved immediately to `config.json`
- New modules automatically added to the end if not in saved configuration

### Error Handling
- Graceful fallback to default order if configuration is corrupted
- Logging of all tab management operations
- Safe handling of missing or invalid module references

## Troubleshooting

### Tabs Not Appearing
- Check if tabs are hidden using the "Show Hidden Tab" menu
- Try "Reset to Default Order" to restore all tabs

### Configuration Issues
- Delete the `ui` section from `config.json` to reset to defaults
- Restart the application after manual config changes

### Performance
- Tab rearrangement is immediate with no performance impact
- Configuration saves are asynchronous and don't block the UI