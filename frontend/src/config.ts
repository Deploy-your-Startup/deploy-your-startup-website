export const cliVersion = "v0.1.0";
export const templateVersion = "v0.1.0";
export const installCommand = `uv tool install --python 3.12 git+https://github.com/Deploy-your-Startup/cli@${cliVersion}`;
export const loginCommand = "gh auth login -h github.com -p https -s repo,workflow,read:packages,write:packages\ngh auth setup-git\nstartup doctor";
export const bootstrapCommand = `startup bootstrap --kind fullstack --provider hetzner --domain-owned --template-version ${templateVersion}`;
