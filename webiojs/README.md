# PyWebIO JS library

## Build

```bash
npm install
npx gulp
```

## Use built js

```bash
cp dist/pywebio.min.* ../pywebio/html/js
```

By default, PyWebIO uses CDN for frontend resources. For local dev build, you also need to set `cdn=False` in `start_server()` or `webio_handler()` in your PyWebIO app to specify the use of the local built js file.