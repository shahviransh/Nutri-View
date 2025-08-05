<div align="center">
  <img src="https://github.com/shahviransh/Nutri-View/blob/main/src-tauri/icons/128x128.png" alt="Logo" width="80" height="80">
  <h3 align="center">Nutri-View</h3>
  <p align="center">
    A cross-platform desktop application for exploring and analyzing Integrated Modeling for Watershed Evaluation of BMPs (IMWEBs) environmental datasets.
    <br />
    <a href="https://github.com/shahviransh/Nutri-View">View on GitHub</a>
  </p>
</div>

<p align="center">
  <a href="https://www.youtube.com/watch?v=KNyyVSygOWY">
    <img src="https://img.youtube.com/vi/KNyyVSygOWY/0.jpg" alt="NutriView Demo" /><br/>🎥 See the application in action (33 mins)
  </a>
</p>

---

## 📚 Table of Contents

<details>
  <summary>Click to expand</summary>
  <ol>
    <li><a href="#-about-the-project">About The Project</a>
      <ul>
        <li><a href="#-key-features">Key Features</a></li>
      </ul>
    </li>
    <li><a href="#%EF%B8%8F-architecture">Architecture</a></li>
    <li><a href="#-getting-started">Getting Started</a>
      <ul>
        <li><a href="#-installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#%EF%B8%8F-common-issues">Common Issues</a></li>
    <li><a href="#-freeing-up-space-after-uninstalling">Freeing Up Space After Uninstalling</a></li>
    <li><a href="#-technical-report">Technical Report</a></li>
    <li><a href="#-acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

---

## 🧠 About The Project

**Nutri-View** is a tool designed for exploring, analyzing, and visualizing environmental model data. It supports both tabular and geospatial data formats and provides features for data filtering, aggregation, calculation, graphing, mapping, and exporting.

NutriView is a new in-house software tool developed by the Canada Water Agency (CWA) to help manage and utilize the large volume of data associated with the implementation of Best Management Practices (BMPs). This work is supported by a $49.4 million (2024–2028) federal investment under the Lake Erie Precision Conservation sub-stream of the Great Lakes Freshwater Ecosystem Initiative (FEI).

The tool integrates headline program performance measures with detailed information on thousands of implemented BMPs. Once deployed on the cloud, NutriView will enable authorized CWA staff to visually explore data, generate dynamic maps, and monitor trends—particularly those related to the transition toward precision conservation approaches for nutrient management.

In addition, NutriView will facilitate secure data sharing with selected and permitted members of the research community, beginning with ECCC Science and Technology (S&T). This will support research, enhance modeling efforts, and help inform CWA’s future programming decisions to restore and protect Lake Erie water quality.

Built with **Tauri**, **Vue 3**, and **Flask**, this application provides a rich, interactive, and offline-capable experience for analyzing tabular and geospatial data.

### 🔑 Key Features

- **Cross-Platform Support:** Packages available for Windows, macOS, and Linux.
- **Dynamic Visualization:** Interactive charts using ECharts and maps using Leaflet.
- **Geospatial Intelligence:** Support for shapefiles, GeoTIFFs, and export to SHP and GeoJSON.
- **Custom Formula Builder:** Combine numerical columns using mathematical expressions.
- **Data Export:** Export tables, graphs, and maps to multiple formats (CSV, TXT, XLSX, PNG, SVG, PDF, SHP).
- **Authentication Support:** Login/logout with JWT-based token security (web mode).
- **Integrated Build Pipeline:** Docker, Makefile, and PowerShell scripts included for CI/CD and version control.

---

## 🏗️ Architecture

<p align="center">
  <a href="https://www.youtube.com/watch?v=x69xOCFa_0c">
    <img src="https://img.youtube.com/vi/x69xOCFa_0c/0.jpg" alt="NutriView Demo" /><br/>🎥 See the application in action (20 mins)
  </a>
</p>

![Diagram](https://github.com/shahviransh/Nutri-View/blob//main/Diagram.png)

### 📦 Structure

- **Frontend (Vue 3):**
  - UI components in `src/components/`
  - Pages like Graphs, Maps, Login, and Help in `src/pages/`
  - Vue Router and Vuex for routing and state management
  - Lightning-fast development and optimized production builds using Vite
- **Backend (Flask):**
  - `apppy.py`: Entry point
  - `routes.py`: API endpoints (data, maps, export, authentication)
  - `services.py`: Data fetching and transformation logic
  - `validate.py`: Request validation
- **Desktop Runtime (Tauri):**
  - Bundled with Rust
  - Defined in `src-tauri/`

---

## 🚀 Getting Started

### 📥 Installation

Download the latest release from the [GitHub Releases Page](https://github.com/shahviransh/Nutri-View/releases/latest).

### Download for your platform

#### 🐧 **Linux**

- **Available Packages**: `.deb`, `.rpm`, or `.AppImage`
  - **`.deb`**: Suitable for Debian-based distributions like **Ubuntu**, **Linux Mint**, or **Kali**. Install with:

    ```bash
    sudo apt install ./<filename>.deb
    ```

  - **`.rpm`**: Suitable for RPM-based distributions like **Fedora**, **Red Hat Enterprise Linux (RHEL)**, or **openSUSE**. Install with:

    ```bash
    sudo rpm -i <filename>.rpm
    ```

  - **`.AppImage`**: Universal package for most distributions. Make it executable using:

    ```bash
    chmod +x <filename>.AppImage
    ./<filename>.AppImage
    ```

- Once installed, you can launch the application from your application menu or terminal.

#### ✅ **Windows**

- **Available Packages**: `.msi` or `.exe`
  - **`.msi`**: Requires admin privileges for installation. Double-click the file and follow the setup instructions. The application will launch automatically after installation.
  - **`.exe`**: Suitable for users without admin rights. Run the `.exe` file, and the application will launch immediately.
- After installation, you can find the application in your Start Menu or Desktop.

#### 🍎 **macOS**

- **Available Packages**: `.dmg` or `.app.tar.gz`
  - **Intel vs ARM**: Check your Mac's architecture before downloading.  
    - **Intel Macs**: Download the **x64** package.  
    - **Apple Silicon (M1/M2)**: Download the **aarch64** package.
  - **`.dmg`**: Open the `.dmg` file, then drag and drop the application into your **Applications** folder. Launch the application from the Applications folder or via Spotlight Search.
  - **`.app.tar.gz`**: Extract the file using:

    ```bash
    tar -xzf <filename>.app.tar.gz
    ```

    Then move the extracted application to your **Applications** folder. Launch the application as usual.

Launch the Application: The application connects the Vue 3 frontend with the Flask backend and should be ready to use.

## ⚠️ Common Issues

### ❌ Can't Find Exported Files or Export Fails: “Permission Denied” or Files Not Saved

If you're trying to **export files (e.g., CSV, PNG, SHP, etc.)**, and the operation fails or you see a **permission error**, it's likely due to **write restrictions** on the default export directory. If you **can’t find the exported files**, see below.

> By default, the backend saves export files **relative to the Nutri-View app’s installation directory**, typically at: `{Nutri-View App Path}/_up_/backend/apppy/_internal/dataExport`

### 💡 Why This Happens

- If the app is installed in a **system directory** (like `/usr/lib/` or `Program Files`), the backend might not have **write access** there **without admin privileges**.
- Since the backend writes export files **relative to its own location**, it fails if that location is **read-only** for the current user.

### ✅ Solution

To avoid export issues:

1. **Change the export path to a folder the user has write access to**, such as:
   - Desktop
   - Downloads
   - Documents
   - A custom folder inside the user's home directory (e.g., `~/IMWEBs-Exports`)

## 🧹 Freeing Up Space After Uninstalling

After uninstalling **Nutri-View**, you can delete leftover temporary files to free up space. Each platform has a **TempFiles** folder in the user data folder that can be safely deleted.

Run the following commands to delete the **TempFiles** folder:

### 🐧 **Linux**

```bash
rm -rf ~/.local/share/Nutri-View/TempFiles
```

### ✅ Windows

```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Nutri-View\TempFiles"
```

### 🍎 macOS

```bash
rm -rf ~/Library/Application\ Support/Nutri-View/TempFiles
```

## 📄 Technical Report

For a detailed explanation of the application's architecture, data processing workflows, and design decisions, please refer to the full technical report:

[👉 Download the Nutri-View Technical Report (.docx)](https://github.com/shahviransh/Nutri-View/raw/refs/heads/main/Technical%20Report.docx)

## 🙌 Acknowledgments

- Core Technologies:
  - Tauri, Rust
  - Vue 3
  - Python, Flask
- Frontend Libraries:
  - Vite
  - ECharts
  - Leaflet
- Python Libraries & Tools:
  - Data Handling & Analysis:
    - `pandas`, `numpy`, `xlsxwriter`, `scipy`, `scikit-learn`
  - Geospatial Processing:
    - `geopandas`, `pyogrio`, `osgeo (gdal, ogr, osr)`, `cmocean`
  - Visualization:
    - `matplotlib`, `cycler`, `PIL (Pillow)`
- Contributors & Community:
  - Special thanks to the following individuals for their guidance, data, and support:
    - Julia Rutledge (CWA)
    - Daniel DeOcampo (CWA)
    - Yongbo Liu (ECCC)
    - Wanhong Yang (UoG)
- Open-Source Maintainers:
  - A heartfelt thank-you to the developers behind the core libraries that power this application.