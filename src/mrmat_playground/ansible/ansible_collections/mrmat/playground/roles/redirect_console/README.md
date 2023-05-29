redirect_console
=========

Redirects journald output to the console

Requirements
------------

None

Role Variables
--------------

| Variable | Default      | Description                                                                  |
|----------|--------------|------------------------------------------------------------------------------|
| redirect | yes          | If set to yes, then configure journald to redirect its output to the console |
| tty      | /dev/ttyAMA0 | The TTY device to redirect the console to                                    |

Dependencies
------------

None

Example Playbook
----------------

```yaml
- hosts: all
  name: Deploy
  roles:
  - name: mrmat.playground.redirect_console
    vars:
      redirect: yes
      tty: /dev/ttyAMA0
```

License
-------

MIT

Author Information
------------------

MrMat
