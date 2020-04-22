## Test
使用 selenium 进行 + percy 进行测试。

测试的原理为使用selenium打开编写的PyWebIO测试服务，在页面上进行模拟操作，
将一些时刻的网页快照使用percy进行保存，percy可以比较不同提交之间的相同页面的区别。

### 编写测试用例
// todo

### 运行测试用例

```bash
pip3 install -e ".[dev]" 
npm install -D @percy/agent
export PERCY_TOKEN=[projects-token]

npx percy exec -- python3 1.basic_output.py auto
```


