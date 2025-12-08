# 🧠 AI DevOps Brain for Enterprise

> Enterprise-grade AIOps simulation platform with 19 industry coverage, AI-powered incident detection, RCA, and auto-remediation capabilities.

[![Status](https://img.shields.io/badge/status-production--ready-green)]()
[![Industries](https://img.shields.io/badge/industries-19-blue)]()
[![Kubernetes](https://img.shields.io/badge/kubernetes-minikube-orange)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

## 🚀 Quick Start

```bash
# 1. Setup local environment
./scripts/setup-local-services.sh

# 2. Deploy all 19 industries
./scripts/setup-all-19-industries.sh

# 3. Start Web UI
./scripts/start-ui.sh

# 4. Run demo scenario
./scripts/run-demo-scenario.sh
```

**UI**: http://localhost:8504

## 📊 Features

- ✅ **19 Industry Simulation** - Finance, Healthcare, Automotive, AI Cloud, GPU Cloud, and more
- ✅ **AI Operator** - Real-time incident detection with RCA and auto-remediation suggestions
- ✅ **Web Dashboard** - Streamlit-based UI for monitoring and analysis
- ✅ **Chaos Testing** - Comprehensive chaos engineering suite
- ✅ **Observability Pipeline** - Multi-namespace metrics and log collection
- ✅ **Industry-Specific Patterns** - Domain-aware failure detection

## 🏗️ Architecture

```
19 Industry Namespaces (43 pods)
    ↓
AI Operator (watches, detects, analyzes)
    ↓
PostgreSQL + Redis + Kafka
    ↓
Web UI (Streamlit Dashboard)
```

## 📚 Documentation

- **Quick Start**: `QUICK_START_VALIDATION.md`
- **Roadmap**: `REFINED_ROADMAP.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Setup Guide**: `LOCAL_SETUP.md`
- **Project Status**: `PROJECT_STATUS.md`

## 🎯 Current Status

- ✅ Infrastructure: 100% Complete
- ✅ AI Operator: 100% Complete
- ✅ Web UI: 100% Complete
- ⏳ AI Models: Ready for Integration

## 🔗 Links

- **Repository**: https://github.com/achavala/AI-DevOps-Brain-for-Enterprise
- **Issues**: Use GitHub Issues for tracking work
- **Wiki**: Project documentation and guides

## 📝 License

MIT License - See LICENSE file for details

