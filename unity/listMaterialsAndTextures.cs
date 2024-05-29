using UnityEngine;
using UnityEditor;
using System.Collections.Generic;
using System.IO;
using System.Linq;

public class MaterialsLister
{
    [MenuItem("Tools/Vircadia/List All Materials and Textures (debug only)")]
    public static void ListMaterialsAndTexturesToFile()
    {
        // Use OpenFolderPanel instead of SaveFilePanel to only get the folder path
        string folderPath = EditorUtility.OpenFolderPanel("Select folder to save materials and textures list", "", "");
        if (!string.IsNullOrEmpty(folderPath))
        {
            string filePath = Path.Combine(folderPath, "MaterialsAndTexturesList.txt");
            ListMaterialsAndTextures(filePath);
        }
    }

    private static void ListMaterialsAndTextures(string filePath)
    {
        string[] allAssets = AssetDatabase.GetAllAssetPaths();
        var materialPaths = allAssets.Where(path => path.StartsWith("Assets/") && path.EndsWith(".mat")).ToList();

        List<string> materialsInfo = new List<string>();
        HashSet<string> uniqueTextures = new HashSet<string>();

        foreach (string materialPath in materialPaths)
        {
            Material material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
            bool isApplied = IsMaterialApplied(material);
            string appliedStatus = isApplied ? "Applied" : "Not Applied";
            materialsInfo.Add($"{materialPath} - {appliedStatus}");

            HashSet<string> processedTextures = new HashSet<string>(); // Track textures for this material to avoid duplicates
            ListTexturesUsedByMaterial(material, materialsInfo, uniqueTextures, processedTextures);

            materialsInfo.Add(""); // Add a space for readability
        }

        materialsInfo.Add($"Total unique textures used = {uniqueTextures.Count}");
        File.WriteAllLines(filePath, materialsInfo);
        Debug.Log($"Materials and textures list saved to {filePath}");
    }

    private static bool IsMaterialApplied(Material material)
    {
        Renderer[] renderers = GameObject.FindObjectsOfType<Renderer>();
        foreach (Renderer renderer in renderers)
        {
            if (renderer.sharedMaterials.Any(m => m == material))
            {
                return true;
            }
        }
        return false;
    }

    private static void ListTexturesUsedByMaterial(Material material, List<string> materialsInfo, HashSet<string> uniqueTextures, HashSet<string> processedTextures)
    {
        Shader shader = material.shader;
        int propertyCount = ShaderUtil.GetPropertyCount(shader);
        for (int i = 0; i < propertyCount; i++)
        {
            if (ShaderUtil.GetPropertyType(shader, i) == ShaderUtil.ShaderPropertyType.TexEnv)
            {
                string propertyName = ShaderUtil.GetPropertyName(shader, i);
                Texture texture = material.GetTexture(propertyName);
                if (texture != null && !processedTextures.Contains(texture.name))
                {
                    materialsInfo.Add($"\t{propertyName}: {texture.name}");
                    processedTextures.Add(texture.name);
                    uniqueTextures.Add(texture.name);
                }
            }
        }
    }
}
