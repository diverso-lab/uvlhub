<div align="center">

  <!-- CI Workflows -->
  <a href="">[![Pytest Testing Suite](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_pytest.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_pytest.yml)</a>
  <a href="">[![Commits Syntax Checker](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_commits.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_commits.yml)</a>
  <a href="">[![Lint](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_lint.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/CI_lint.yml)</a>

  <!-- CD Workflows -->
  <a href="">[![DockerHub Deployment](https://github.com/diverso-lab/uvlhub/actions/workflows/CD_dockerhub.yml/badge.svg)](https://github.com/diverso-lab/uvlhub/actions/workflows/CD_dockerhub.yml)</a>
  <a href="">[![Webhook Deployment](https://github.com/diverso-lab/uvlhub/actions/workflows/CD_webhook.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/CD_webhook.yml)</a>

</div>


<div style="text-align: center; margin-top: 10px">
  <img src="https://www.uvlhub.io/static/media/logos/default.svg" alt="Logo">
</div>

# uvlhub.io

Repository of feature models in UVL format integrated with Zenodo and flamapy following Open Science principles - Developed by DiversoLab

## Official documentation

You can consult the official documentation of the project at [docs.uvlhub.io](https://docs.uvlhub.io/)

### Installation

Follow all steps of **Installation** in the official documentation. When you arrive to this step:
```
pip install -e ./
```
Please, do also:
```
pip install -e ./fm_generator
```
To download changes from fm_generator plugin, please do from the root of the project:
```
cd fm_generator
git pull origin main
git submodule update --init --recursive
```
You also need to install some dependencies with npm:
```
npm install jszip file-saver
npm install
```
To let pyodide work properly:
```
npx webpack --config app/modules/generator/assets/js/webpack.config.js
```
Then, keep on the next step naturally from the official documentation.
