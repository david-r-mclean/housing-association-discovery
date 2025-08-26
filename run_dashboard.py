#!/usr/bin/env python3
"""
Launch the Housing Association Intelligence Dashboard
"""

import uvicorn
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

if __name__ == "__main__":
    print("🚀 Starting Housing Association Intelligence Dashboard")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("🔄 WebSocket real-time updates enabled")
    print("=" * 60)
    
    # Run without reload to avoid the warning
    uvicorn.run("dashboard.app:app", host="0.0.0.0", port=8000, reload=False)
