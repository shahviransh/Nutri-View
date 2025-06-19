import fs from "fs";
import path from "path";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);


// Source paths for the bundled MSI and EXE files
const msiSource = path.join(__dirname, "target", "release", "bundle", "msi");
const nsisSource = path.join(__dirname, "target", "release", "bundle", "nsis");

// Destination path
const destination = path.join(__dirname, "target", "release");

// Move files function
function moveFiles(sourcePath, destPath) {
  fs.readdir(sourcePath, (err, files) => {
    if (err) {
      console.error("Failed to read directory: ${sourcePath}");
      return;
    }
    files.forEach((file) => {
      const oldPath = path.join(sourcePath, file);
      const newPath = path.join(destPath, file);
      fs.rename(oldPath, newPath, (renameErr) => {
        if (renameErr) {
          console.error(`Failed to move file ${file}:`, renameErr);
        } else {
          console.log(`Moved ${file} to ${destPath}`);
        }
      });
    });
  });
}

// Move MSI and NSIS files
moveFiles(msiSource, destination);
moveFiles(nsisSource, destination);
