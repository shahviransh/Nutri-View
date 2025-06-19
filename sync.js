import fs from "fs";
import path from "path";
import { dirname } from "path";
import { fileURLToPath } from "url";
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
import JSON5 from 'json5';

// Read the package.json5 file
const packageJson5 = fs.readFileSync('./package.json5', 'utf-8');

// Parse the JSON5 content
const packageJson1 = JSON5.parse(packageJson5);

// Write the standard JSON content to package.json
fs.writeFileSync('./package.json', JSON.stringify(packageJson1, null, 2), 'utf-8');

console.log('package.json5 converted to package.json');

// Paths to package.json and Cargo.toml
const packageJsonPath = path.join(__dirname, "package.json");
const cargoTomlPath = path.join(__dirname, "src-tauri", "Cargo.toml");

// Read version from package.json
const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));
const version = packageJson.version;

// Read Cargo.toml and update the version
let cargoToml = fs.readFileSync(cargoTomlPath, "utf8");
cargoToml = cargoToml.replace(/version = ".*"/, `version = "${version}"`);
fs.writeFileSync(cargoTomlPath, cargoToml);

console.log(`✅ Synced Cargo.toml version to ${version}`);