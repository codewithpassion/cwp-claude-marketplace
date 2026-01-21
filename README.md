# cwp-claude-marketplace

A Claude Code plugin marketplace for discovering and installing plugins.

## Overview

This marketplace serves as a catalog of Claude Code plugins that can be easily discovered and installed by users.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| `cwp-claude-framework` | Personal toolkit of reusable Claude commands and utilities |
| `cwp-how-i-vibe` | Dom's step by step framework for agentic engineering |

## Prerequisites

- Claude Code version 1.0.33 or later (run `claude --version` to check)
- If you don't see the `claude plugin` command, update Claude Code to the latest version

## Quick Install

Install the marketplace and all plugins with a single command:

```bash
curl -fsSL https://raw.githubusercontent.com/codewithpassion/cwp-claude-marketplace/main/install.sh | bash
```

This will show the commands to be executed and ask for confirmation before proceeding.

### cc-mirror Support

If you have [cc-mirror](https://github.com/anthropics/cc-mirror) installed, the script will automatically detect your variants and prompt you to choose which Claude command to use:

```
cc-mirror detected!

Available Claude commands:

  1) claude (default)
  2) mclaude (mirror)
  3) zclaude (zai)

Which command do you want to use? [1-3]
```

### Options

Specify the Claude command directly:

```bash
curl -fsSL ... | bash -s -- --cmd mclaude
```

Specify the installation scope:

```bash
curl -fsSL ... | bash -s -- --scope project
```

Combine options:

```bash
curl -fsSL https://raw.githubusercontent.com/codewithpassion/cwp-claude-marketplace/main/install.sh | bash -s -- --cmd zclaude --scope user
```

## Manual Installation

### From the Command Line

Run these commands from your terminal:

```bash
# Add the marketplace
claude plugin marketplace add codewithpassion/cwp-claude-marketplace

# Install individual plugins
claude plugin install cwp-claude-framework@cwp-claude-marketplace
claude plugin install cwp-how-i-vibe@cwp-claude-marketplace
```

### From Within Claude Code

You can also use slash commands from within a Claude Code session:

```
/plugin marketplace add codewithpassion/cwp-claude-marketplace
/plugin install cwp-claude-framework@cwp-claude-marketplace
```

### Browse Available Plugins

**From command line:**

```bash
claude plugin list
```

**From within Claude Code:**

Run `/plugin` to open the plugin manager, then navigate to the **Discover** tab.

## Managing Plugins

### View Installed Plugins

```bash
claude plugin list --installed
```

Or from within Claude Code, run `/plugin` and navigate to the **Installed** tab.

### Enable/Disable Plugins

```bash
claude plugin disable cwp-claude-framework@cwp-claude-marketplace
claude plugin enable cwp-claude-framework@cwp-claude-marketplace
```

### Uninstall Plugins

```bash
claude plugin uninstall cwp-claude-framework@cwp-claude-marketplace
```

### Update Marketplace

To fetch the latest plugin listings:

```bash
claude plugin marketplace update cwp-claude-marketplace
```

## Structure

```
cwp-claude-marketplace/
├── .claude-plugin/
│   └── marketplace.json     # Marketplace manifest
├── plugins/                  # Local plugins directory
├── install.sh               # Quick installer script
└── README.md
```

## Adding Plugins to the Marketplace

Edit `.claude-plugin/marketplace.json` to add plugins to the `plugins` array.

### Local Plugin Entry

For plugins stored in the `plugins/` directory:

```json
{
  "name": "plugin-name",
  "source": "./plugins/plugin-name",
  "description": "What the plugin does",
  "version": "1.0.0"
}
```

### External GitHub Plugin

For plugins hosted on GitHub:

```json
{
  "name": "external-plugin",
  "source": { "source": "github", "repo": "owner/repo" }
}
```

## Troubleshooting

### `/plugin` command not recognized

1. Check your version: `claude --version` (requires 1.0.33 or later)
2. Update Claude Code to the latest version
3. Restart Claude Code

### Marketplace not loading

- Verify the URL or path is accessible
- Check that `.claude-plugin/marketplace.json` exists

### Plugin installation failures

- Check that plugin source URLs are accessible
- For GitHub sources, ensure repositories are public or you have access

## License

MIT
