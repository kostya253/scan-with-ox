Hello,

If you want to integrate the OX scanner into your GitHub Action pipelines, you can use this Python program.

Modify the following parameters:

1. ACCESS_TOKEN - insert your GitHub token to allow the pipeline scanner to insert the GitHub Actions YAML file. repo/workflow/user permissions required
2. ox_host_url - insert your self-hosted OX server URL to allow the scanner to connect to your OX instance.
3. [optionally] - if running self-hosted GitHub, supply a `--github-api` argument so that the action connects properly to your GH instance.

For additional options, please refer to this link: https://github.com/oxsecurity/ox-security-scan, if you decide to make changes to the YAML file contents.

## Usage

GitHub SaaS:
`python main.py`

Self-hosted GitHub:
`python main.py --github-api "gh-server.mycompany.com"`
