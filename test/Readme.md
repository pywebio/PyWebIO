## Test

```bash
pip3 install -e ".[dev]" 
npm install --save-dev @percy/agent
export PERCY_TOKEN=[projects-token]

percy exec -- python3 1.basic_output.py auto
```


