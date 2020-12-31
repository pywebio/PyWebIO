Other
============

.. _codemirror_options:

常用的Codemirror选项
--------------------

* ``mode`` (str): 代码语言。支持的语言有：https://codemirror.net/mode/index.html
* ``theme`` (str): 编辑器主题。可使用的主题：https://codemirror.net/demo/theme.html
* ``lineNumbers`` (bool): 是否显示行号
* ``indentUnit`` (int): 缩进使用的空格数
* ``tabSize`` (int): 制表符宽度
* ``lineWrapping`` (bool): 是否换行以显示长行


.. _nginx_ws_config:

Nginx WebSocket配置示例
-----------------------

假设后端服务器运行在 ``localhost:5000`` 地址，并将PyWebIO的后端接口绑定到 ``/tool/io`` 路径上，则通过Nginx访问PyWebIO服务的配置如下::

    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }

    server {
        listen 80;

        location /tool/ {
            alias /path/to/pywebio/static/dir/;
        }
        location /tool/io {
             proxy_read_timeout 300s;
             proxy_send_timeout 300s;
             proxy_http_version 1.1;
             proxy_set_header Upgrade $http_upgrade;
             proxy_set_header Connection $connection_upgrade;
             proxy_pass http://localhost:5000;
        }
    }

以上配置文件将PyWebIO的静态文件托管到 ``/tool/`` 目录下， 并将 ``/tool/io`` 反向代理到 ``localhost:5000``

.. note::
    使用以上配置文件后，您还需要在 ``webio_handler`` 或 ``start_server`` 函数中将nginx绑定的域名添加到 ``allowed_origins`` 参数指定的列表中


PyWebIO的静态文件的路径可使用命令 ``python3 -c "import pywebio; print(pywebio.STATIC_PATH)"`` 获得，你也可以将静态文件复制到其他目录下::

    cp -r `python3 -c "import pywebio; print(pywebio.STATIC_PATH)"` ~/web
