import installer from "../public/install.sh?raw";

// install.sh pins the template version; the site shows the same one.
const pinned = (name: string) => {
  const version = installer.match(new RegExp(`^${name}="(v\\d+\\.\\d+\\.\\d+)"$`, "m"))?.[1];
  if (!version) throw new Error(`install.sh does not pin ${name}`);
  return version;
};
export const templateVersion = pinned("startup_template_version");
export const installCommand = "curl -fsSL https://deploy-your-startup.com/install.sh | bash";
export const loginCommand = "gh auth login -h github.com -p https -s repo,workflow,read:packages,write:packages\ngh auth setup-git\nstartup doctor";
export const bootstrapCommand = `startup bootstrap --kind fullstack --provider hetzner --domain-owned --template-version ${templateVersion}`;

export const onboardingCommand = "curl -fsSL https://deploy-your-startup.com/install.sh | bash -s -- --onboard";
