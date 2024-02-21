using UnityEngine;
using UnityEditor;
using System.IO;
using System.Text;
using System.Collections.Generic;
using System.Linq;

public class LightmapInfoLogger
{
    private static Dictionary<int, string> reflectionProbeTextures = new Dictionary<int, string>();
    private static string texturesFolderPath;

    [MenuItem("Tools/Vircadia/Get Lightmap Information")]
    public static void GetLightmapInformation()
    {
        string folderPath = EditorUtility.SaveFolderPanel("Choose Location to Save Lightmap Info", "", "");
        if (!string.IsNullOrEmpty(folderPath))
        {
            CacheReflectionProbeTextures();
            LogAllMeshObjectsLightmapInfo(folderPath);
        }
    }

    private static void CacheReflectionProbeTextures()
    {
        reflectionProbeTextures.Clear();

        if (LightmapSettings.lightmaps.Length > 0)
        {
            string firstLightmapPath = AssetDatabase.GetAssetPath(LightmapSettings.lightmaps[0].lightmapColor);
            texturesFolderPath = Path.GetDirectoryName(firstLightmapPath);
            string absolutePath = GetAbsolutePath(texturesFolderPath);
            var allTextures = Directory.GetFiles(absolutePath, "*.*", SearchOption.TopDirectoryOnly)
                .Where(s => s.EndsWith(".exr") || s.EndsWith(".hdr"));

            foreach (var texturePath in allTextures)
            {
                string fileName = Path.GetFileNameWithoutExtension(texturePath);
                if (fileName.ToLower().Contains("reflectionprobe"))
                {
                    int index = ExtractNumberFromName(fileName);
                    if (!reflectionProbeTextures.ContainsKey(index))
                    {
                        reflectionProbeTextures[index] = Path.GetFileName(texturePath);
                    }
                }
            }
        }
    }

    private static int ExtractNumberFromName(string name)
    {
        var match = System.Text.RegularExpressions.Regex.Match(name, @"\d+");
        return match.Success ? int.Parse(match.Value) : -1;
    }

    private static void LogAllMeshObjectsLightmapInfo(string folderPath)
    {
        StringBuilder sb = new StringBuilder();
        MeshRenderer[] allMeshRenderers = Object.FindObjectsOfType<MeshRenderer>();
        int total = allMeshRenderers.Length;

        for (int i = 0; i < total; i++)
        {
            MeshRenderer renderer = allMeshRenderers[i];
            EditorUtility.DisplayProgressBar("Logging Lightmap Info", $"Processing {renderer.gameObject.name} ({i + 1}/{total})", (float)i / total);

            if (renderer.lightmapIndex != -1)
            {
                sb.AppendLine("Object: " + renderer.gameObject.name);
                LightmapIndexInfo(renderer, sb);
                sb.AppendLine();
            }
        }

        WriteToFile(sb.ToString(), folderPath);
    }

    private static void LightmapIndexInfo(Renderer renderer, StringBuilder sb)
    {
        int lightmapIndex = renderer.lightmapIndex;
        sb.AppendLine("Lightmap Index: " + lightmapIndex);
        if (lightmapIndex != -1 && LightmapSettings.lightmaps.Length > lightmapIndex)
        {
            LightmapData lightmapData = LightmapSettings.lightmaps[lightmapIndex];
            string lightmapPath = AssetDatabase.GetAssetPath(lightmapData.lightmapColor);
            sb.AppendLine("Lightmap Texture: " + lightmapData.lightmapColor.name + Path.GetExtension(lightmapPath));
            
            if (lightmapData.lightmapDir != null)
            {
                string dirLightmapPath = AssetDatabase.GetAssetPath(lightmapData.lightmapDir);
                sb.AppendLine("Directional Lightmap Texture: " + lightmapData.lightmapDir.name + Path.GetExtension(dirLightmapPath));
            }
            else
            {
                sb.AppendLine("No directional lightmap applied.");
            }

            if (reflectionProbeTextures.TryGetValue(lightmapIndex, out string reflectionProbeTexture))
            {
                sb.AppendLine($"Reflection Probe Texture: {reflectionProbeTexture}");
            }
            else
            {
                sb.AppendLine("No associated reflection probe texture found.");
            }

            sb.AppendLine($"Path: {GetAbsolutePath(texturesFolderPath)}");
        }
        else
        {
            sb.AppendLine("No lightmap applied.");
        }
    }

    private static string GetAbsolutePath(string relativePath)
    {
        return Application.dataPath.Substring(0, Application.dataPath.LastIndexOf("Assets")) + relativePath;
    }

    private static void WriteToFile(string content, string folderPath)
    {
        string filePath = Path.Combine(folderPath, "LightmapInfo.txt");
        File.WriteAllText(filePath, content);

        EditorUtility.ClearProgressBar();
        EditorUtility.DisplayDialog("Lightmap Info Logger", "Lightmap info has been saved to LightmapInfo.txt.", "OK");

        Debug.Log("Lightmap info saved to: " + filePath);
    }
}
