using UnityEngine;
using UnityEditor;
using System.IO;
using System.Collections.Generic;

public class MaterialChecker
{
    [MenuItem("Tools/Vircadia/Prep Materials for Export to Blender")]
    public static void PrepMaterialsForExport()
    {
        string folderPath = EditorUtility.OpenFolderPanel("Choose Folder for Report", "", "");
        if (!string.IsNullOrEmpty(folderPath))
        {
            CheckMaterials(folderPath);
        }
        else
        {
            Debug.Log("Operation cancelled or no folder selected.");
        }
    }

    static void CheckMaterials(string checksFolderPath)
    {
        string filePath = Path.Combine(checksFolderPath, "MaterialsCheckReport.txt");
        List<string> lines = new List<string>();

        Renderer[] renderers = GameObject.FindObjectsOfType<Renderer>(true); // Include inactive objects
        foreach (Renderer renderer in renderers)
        {
            foreach (Material material in renderer.sharedMaterials)
            {
                if (material == null) continue;

                // Check and report materials not using URP shaders
                if (!material.shader.name.Contains("Universal Render Pipeline"))
                {
                    lines.Add($"Material '{material.name}' uses shader '{material.shader.name}' which is not part of URP.");
                    // Attempt to correct non-URP materials
                    if (material.shader.name == "Shader Graphs/TransparentCutoutUnlit" || material.shader.name == "Shader Graphs/TransparentCutoutLit")
                    {
                        material.shader = Shader.Find("Universal Render Pipeline/Lit");
                        material.SetFloat("_WorkflowMode", 1); // Set to Metallic
                        material.SetFloat("_Surface", 0); // Set to Opaque
                        lines.Add($"Corrected Material '{material.name}': Shader changed to URP/Lit, Workflow Mode to Metallic, Surface Type to Opaque.");
                    }
                }
                else if (material.shader.name.Contains("Universal Render Pipeline/Lit"))
                {
                    // Handle Specular to Metallic workflow transition
                    Texture relevantTexture = FindSpecularOrGlossTexture(material);
                    if (material.HasProperty("_WorkflowMode") && material.GetFloat("_WorkflowMode") == 0 && relevantTexture != null) // Assuming 0 represents Specular
                    {
                        material.SetFloat("_WorkflowMode", 1); // Set to Metallic
                        material.SetTexture("_MetallicGlossMap", relevantTexture);
                        lines.Add($"Modified Material '{material.name}': Texture with 'gloss' or 'spec' in name moved to Metallic Map, Workflow Mode changed to Metallic.");
                    }
                }
            }
        }

        if (lines.Count == 0)
        {
            lines.Add("No materials required modification.");
        }
        else
        {
            lines.Insert(0, "Material Modifications Report:");
        }

        File.WriteAllLines(filePath, lines.ToArray());
        AssetDatabase.Refresh();

        Debug.Log($"Materials check report generated at {filePath}");
    }

    static Texture FindSpecularOrGlossTexture(Material material)
    {
        Shader shader = material.shader;
        int propertyCount = ShaderUtil.GetPropertyCount(shader);
        for (int i = 0; i < propertyCount; i++)
        {
            if (ShaderUtil.GetPropertyType(shader, i) == ShaderUtil.ShaderPropertyType.TexEnv)
            {
                string propertyName = ShaderUtil.GetPropertyName(shader, i);
                Texture texture = material.GetTexture(propertyName);
                if (texture != null && (texture.name.ToLowerInvariant().Contains("gloss") || texture.name.ToLowerInvariant().Contains("spec")))
                {
                    return texture;
                }
            }
        }
        return null;
    }
}
