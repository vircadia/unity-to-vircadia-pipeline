# Unity to Vircadia Pipeline

These packages are designed to allow the export of scenes from Unity to Vircadia.

## Usage

You'll need:

- Unity 2021.3.4.f1

  - gltfast package (by name, `com.unity.cloud.gltfast`)
  - Unity2Vircadia package **(this repo)**

- Blender 4.0.2 or newer
  - UnityToVircadia Blender addon **(this repo)**

### Step 1. Unity

1. Open your project in Unity `2021.3.4.f1`
2. Install `gltfast` package by name via the "Package Manager" found under the "Window" menu.
3. Install the `Unity2Vircadia` custom package by select the "Assets" menu and `Import Package/Custom Package`
4. A new "Tools" menu will appear in the menu bar with the submenu "Vircadia"
5. From within the menu run "Get Lightmap Information" and select a folder to save the output to.
6. From within the menu run "Prep Materials for Export to Blender" and select the same output folder.
7. From within the File menu navigate to "Export Scene" and choose `glTF-binary (.glb)`

### Step 2. Blender

1. Start a new scene and delete any default content (cube, camera, light, etc.)
2. Install the `UnityToVircadia` Blender plugin by going to "Edit/Preferences," select the "Add-on" tab and press the "Install" button. Select the `Unity2Vircadia.zip` file and Press "Install Add-on". Press the check checkbox to enable the plugin. This will create a `UnityToVircadia` tab on the N panel.
3. Open the `UnityToVircadia` tab on the N Panel
4. Select "Import glTF 2.0" and Import the `.glb` file you exported from Unity
5. Press "Correct Scale" Button"
6. Press "Import Lightmap Info" and a dialog will open. Select the "LightmapInfo.txt" file from the folder we created earlier. This will generate a mesh container for the lightmaps called "vircadia_lightmapData." \* Note: At the moment you will not see these lightmaps until export
7. Press "Adjust Shaders" to correct material properties and repeats.
8. Press the "Export glTF 2.0 button to export your model. Set your format to `glTF Binary (.glb)`. From within the export dialog, open the "include" tab and be sure "Custom Properties" is selected. We recommend setting your Material Image format to `Webp` and checking "Create Webp". Compression can be used as well to lower file size, but minor artifacts may appear. Export `glTF 2.0`.

You are now ready to upload your `.glb` file to the public folder. An S3 bucket is recommended. Amazon (AWS), Digital Ocean, Linode, and more all offer S3 compatible storage.

## Notes

- Use URP shaders with a "Metallic" workflow. Specular is not recommended and may cause visual inconsistencies.

## Developer

### Blender

To make ready the Blender addon, simply wrap the `blender/UnityToVircadia` folder in a second folder named `UnityToVircadia_BlenderAddon`, then zip that folder and install it as an addon in Blender. The `__init__.py` file is the entry point for the plugin.

The final structure should look like this:

```
UnityToVircadia_BlenderAddon.zip
  - UnityToVircadia_BlenderAddon
    - UnityToVircadia
      - __init__.py
      - ...
```

For example,

### Unity

...
