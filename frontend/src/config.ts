export const pitchTemplateVersion = "v0.1.0";

export const installCommand = "curl -fsSL https://deploy-your-startup.com/install.sh | bash";
export const loginCommand = "gh auth login -h github.com -p https -s repo,workflow,read:packages,write:packages\ngh auth setup-git\nstartup doctor";
export const bootstrapCommand = `startup bootstrap --kind fullstack --provider hetzner`;

export const onboardingCommand = "curl -fsSL https://deploy-your-startup.com/install.sh | bash -s -- --onboard";
export const pitchCommand = `${installCommand}\ngh auth login -h github.com -p https -s repo,workflow\ngh auth setup-git\nstartup bootstrap --kind pitch --template-version ${pitchTemplateVersion}`;
