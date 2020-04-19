## Test

```bash
pip3 install -e ".[dev]" 
npm install -D @percy/agent
export PERCY_TOKEN=[projects-token]

npx percy exec -- python3 1.basic_output.py auto
```


