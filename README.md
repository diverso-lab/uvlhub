<div align="center">

  <a href="">[![Pytest Testing Suite](https://github.com/diverso-lab/uvlhub/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/tests.yml)</a>
  <a href="">[![Commits Syntax Checker](https://github.com/diverso-lab/uvlhub/actions/workflows/commits.yml/badge.svg?branch=main)](https://github.com/diverso-lab/uvlhub/actions/workflows/commits.yml)</a>
  
</div>

<div style="text-align: center;">
  <img src="https://www.uvlhub.io/static/img/logos/logo-light.svg" alt="Logo">
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
```
You also need to install some dependencies with npm:
```
npm install jszip file-saver
```
Then, keep on the next step naturally from the official documentation.
