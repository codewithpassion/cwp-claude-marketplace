# cwp-claude-marketplace

A Claude Code plugin marketplace for discovering and installing plugins.

## Overview

This marketplace serves as a catalog of Claude Code plugins that can be easily discovered and installed by users.

## Structure

```
cwp-claude-marketplace/
├── .claude-plugin/
│   └── marketplace.json     # Marketplace manifest
├── plugins/                  # Local plugins directory
└── README.md
```

## Usage

### Adding this Marketplace

```bash
/plugin marketplace add /path/to/cwp-claude-marketplace
```

Or if hosted on GitHub:

```bash
/plugin marketplace add owner/cwp-claude-marketplace
```

### Listing Available Plugins

```bash
/plugin
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

## License

MIT
