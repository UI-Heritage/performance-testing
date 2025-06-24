
# Load Testing Setup

## Prerequisites

- Install K6: https://k6.io/docs/get-started/installation/
- Install Python 3.7+

## How to Run

### 1. Run Load Test
```bash
k6 run --compatibility-mode=base --out json=load-test-results.json load-test.js
```

### 2. Process Results
```bash
python process-load-test-result.py load-test-results.json
```