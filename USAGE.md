# FLAC Music Store - Usage Guide

## 🎯 One-Click Commands

### Start the Application
```bash
./run.sh
```
This will automatically:
- Set up all dependencies
- Start both backend and frontend
- Display access URLs

### Stop the Application  
```bash
./stop.sh
```
This will cleanly stop all running services.

## 🌐 Access Points

Once running, visit:
- **Main App**: http://localhost:8000
- **API Backend**: http://localhost:5000
- **API Test**: http://localhost:5000/api/test

## 🔧 Troubleshooting

### Missing Dependencies
If you see Python venv errors:
```bash
sudo apt install python3.12-venv python3-pip
```

### Port Conflicts  
The script automatically finds available ports if defaults are busy.

### Stopping Stuck Services
```bash
pkill -f "python.*app.py"
pkill -f "python.*http.server"
```

## 📁 Project Structure
```
flacmusicstore/
├── run.sh          # 🚀 Start everything  
├── stop.sh         # 🛑 Stop everything
├── backend/        # Flask API server
├── frontend/       # Static web files
└── README.md       # Full documentation
```

That's it! Just run `./run.sh` and you're ready to go! 🎵 