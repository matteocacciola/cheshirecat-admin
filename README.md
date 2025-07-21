# Cheshire Cat Admin UI

A modern web-based administration interface for the [Cheshire Cat Core](https://github.com/matteocacciola/cheshirecat-core) framework. This admin UI provides a user-friendly interface to manage, configure, and monitor your Cheshire Cat AI assistant instances.

## Features

- 🎯 **Dashboard Overview** - Real-time monitoring of Cheshire Cat instances
- 🔧 **Configuration Management** - Easy-to-use interface for system settings
- 🧩 **Plugin Management** - Install, configure, and manage plugins
- 👥 **User Management** - Handle user accounts and permissions
- 📊 **Analytics & Logs** - Monitor conversations and system performance
- 🔐 **Authentication & Security** - Secure access control and user management
- 🎨 **Modern UI** - Clean, responsive interface built with modern web technologies

## Prerequisites

- Python 3.11 or higher
- pip and venv for dependency management
- Running instance of [Cheshire Cat Core](https://github.com/matteocacciola/cheshirecat-core)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/matteocacciola/cheshirecat-admin.git
cd cheshirecat-admin
```

### 2. Create and activate virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
make install
```

### 4. Set up environment variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your settings.

### 5. Run the application

```bash
make run
```

The admin interface will be available at `http://localhost:8501`

## Configuration

### Connecting to Cheshire Cat Core

The admin UI connects to your Cheshire Cat Core instance via REST API. Configure the connection in your `.env` file:

```env
CHESHIRE_CAT_API_URL=http://your-cheshire-cat-instance:1865
CHESHIRE_CAT_API_KEY=your-api-key
```

### Authentication

The admin interface supports multiple authentication methods:

- **Local authentication**: Username/password stored in the admin database
- **JWT tokens**: Secure token-based authentication
- **Integration with Cheshire Cat Core**: Sync users from your Cat instance

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

## License

This project is licensed under [GPL3](LICENSE).

## Support

- 📖 [Documentation](https://docs.cheshirecat.ai/admin)
- 🐛 [Issue Tracker](https://github.com/matteocacciola/cheshirecat-admin/issues)
- 📧 [Email Support](mailto:matteo.cacciola@gmail.com)

## Acknowledgments

- [Cheshire Cat Core](https://github.com/matteocacciola/cheshirecat-core) - The AI framework this admin interface manages
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework for building APIs

---

**Made with ❤️ for the Cheshire Cat community**