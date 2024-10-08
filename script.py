from Autodesk.Revit.DB import (
    FilteredElementCollector,
    Transaction,
    ViewDrafting,
    ElementId,
    ElementTransformUtils,
    Transform,
    OpenOptions,
    ModelPathUtils,
    FilePath,
    CopyPasteOptions,
    DetachFromCentralOption,
    BuiltInCategory,
    ElementMulticategoryFilter,
)
from pyrevit import revit, DB, forms
import Autodesk.Revit.DB as DB
import clr
clr.AddReference("System")
from System.Collections.Generic import List, Dictionary
import os

ui = __revit__.ActiveUIDocument

# Function to get a dictionary of drafting view names and their elements
def get_drafting_views_dict(doc):
    drafting_views_dict = {}
    collector = FilteredElementCollector(doc).OfClass(ViewDrafting).WhereElementIsNotElementType()
    for view in collector:
        if not view.IsTemplate:
            drafting_views_dict[view.Name] = view
    return drafting_views_dict

# Function to load the master document
def load_master_document(master_path):
    app = __revit__.Application  # Correctly access the Revit Application
    if not os.path.exists(master_path):
        forms.alert(
            "Master document not found at: {}".format(master_path),
            title="Error",
            warn_icon=True
        )
        return None
    # Open the master document
    try:
        model_path = ModelPathUtils.ConvertUserVisiblePathToModelPath(master_path)
        open_options = OpenOptions()
        # Set detach from central option if necessary
        open_options.DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets
        master_doc = app.OpenDocumentFile(model_path, open_options)
        return master_doc
    except Exception as e:
        forms.alert(
            "Failed to open master document.\nError: {}".format(e),
            title="Error",
            warn_icon=True
        )
        return None

# Function to delete all elements in a drafting view
def delete_elements_in_view(doc, view):
    # Define the categories to delete
    categories_to_delete = [
        BuiltInCategory.OST_Lines,             # Detail Lines
        BuiltInCategory.OST_DetailComponents,  # Detail Components
        BuiltInCategory.OST_FilledRegion,      # Filled Regions (includes Masking Regions)
        BuiltInCategory.OST_TextNotes,         # Text Notes
        BuiltInCategory.OST_Dimensions,        # Dimensions
        BuiltInCategory.OST_GenericAnnotation, # Generic Annotations
        BuiltInCategory.OST_InsulationLines,   # Insulation Lines
        BuiltInCategory.OST_KeynoteTags,      # Keynote Tags
        BuiltInCategory.OST_MaterialTags,     # Material Tags
        # any additional categories ??
    ]
    
    # Create a .NET List[BuiltInCategory]
    categories_list = List[BuiltInCategory]()
    for cat in categories_to_delete:
        categories_list.Add(cat)
    
    # Create a multi-category filter
    category_filter = ElementMulticategoryFilter(categories_list)
    
    # Collect elements owned by the view and matching the categories
    collector = FilteredElementCollector(doc) \
        .OwnedByView(view.Id) \
        .WherePasses(category_filter) \
        .WhereElementIsNotElementType()
    
    # Collect the element Ids
    ids_to_delete = List[ElementId]([e.Id for e in collector])
    
    if ids_to_delete.Count > 0:
        doc.Delete(ids_to_delete)
    print(ids_to_delete)


# Function to copy elements from master view to current view
def copy_elements_from_master(doc, master_doc, master_view, current_view):
    # Define the categories to copy (should match the categories in delete_elements_in_view)
    categories_to_copy = [
        BuiltInCategory.OST_Lines,             # Detail Lines
        BuiltInCategory.OST_DetailComponents,  # Detail Components
        BuiltInCategory.OST_FilledRegion,      # Filled Regions 
        BuiltInCategory.OST_TextNotes,         # Text Notes
        BuiltInCategory.OST_Dimensions,        # Dimensions
        BuiltInCategory.OST_GenericAnnotation, # Generic Annotations
        BuiltInCategory.OST_InsulationLines,   # Insulation Lines
        BuiltInCategory.OST_KeynoteTags,      # Keynote Tags
        BuiltInCategory.OST_MaterialTags,     # Material Tags
        BuiltInCategory.OST_DetailComponentsHiddenLines, 
        BuiltInCategory.OST_DetailComponentTags,	
        BuiltInCategory.OST_MultiCategoryTags,
        BuiltInCategory.OST_Tags,
        BuiltInCategory.OST_RasterImages,
        BuiltInCategory.OST_CalloutLeaderLine,
        BuiltInCategory.OST_MaskingRegion,
        BuiltInCategory.OST_GenericAnnotation,
        BuiltInCategory.OST_IOSDetailGroups,
        BuiltInCategory.OST_IOSArrays,
        BuiltInCategory.OST_ReferenceLines,
        #BuiltInCategory.OST_GenericLines,
        #BuiltInCategory.OST_InvisibleLines,
        #BuiltInCategory.OST_SketchLines,
        #BuiltInCategory.OST_Curves,
        #BuiltInCategory.OST_RepeatingDetailLines,
        #BuiltInCategory.OST_IOSAttachedDetailGroups,
        #BuiltInCategory.OST_SketchLines,
        #BuiltInCategory.OST_IOSDatumPlane,
        #BuiltInCategory.OST_IOSConstructionLine,	
        #BuiltInCategory.OST_IOSAlignmentGraphics,	
        #BuiltInCategory.OST_IOSAligningLine,

        #  any additional categories ??
    ]
    
    # Create a .NET List[BuiltInCategory]
    categories_list = List[BuiltInCategory]()
    for cat in categories_to_copy:
        categories_list.Add(cat)
    
    # Create a multi-category filter
    category_filter = ElementMulticategoryFilter(categories_list)
    
    # Collect elements in the master view matching the categories
    collector = FilteredElementCollector(master_doc, master_view.Id) \
        .WherePasses(category_filter) \
        .WhereElementIsNotElementType()
    
    # Get the element IDs
    master_element_ids = collector.ToElementIds()
    
    # Convert to .NET ICollection<ElementId>
    elements_to_copy = List[ElementId](master_element_ids)
    
    if elements_to_copy.Count == 0:
        print("No elements to copy from master view '{}'.".format(master_view.Name))
        return
    
    # Create a mapping between the source view and destination view
    view_mapping = Dictionary[ElementId, ElementId]()
    view_mapping[master_view.Id] = current_view.Id
    
    # Perform the copy operation
    copy_options = CopyPasteOptions()
    try:
        copied_elements = ElementTransformUtils.CopyElements(
            master_view,
            elements_to_copy,
            current_view,
            Transform.Identity,
            copy_options
        )
        print("Successfully copied elements from '{}' to '{}'.".format(master_view.Name, current_view.Name))
    except Exception as e:
        forms.alert(
            "Failed to copy elements from master view '{}' to current view '{}'.\nError: {}".format(
                master_view.Name, current_view.Name, e
            ),
            title="Error",
            warn_icon=True
        )

# Function to compare and update drafting views
def update_drafting_views_from_master(master_doc, current_doc):
    master_views_dict = get_drafting_views_dict(master_doc)
    current_views_dict = get_drafting_views_dict(current_doc)

    # Start transaction in master_doc
    trans_master = Transaction(master_doc, "Prepare Elements for Copy")
    trans_master.Start()

    try:
        for view_name, master_view in master_views_dict.items():
            if view_name in current_views_dict:
                current_view = current_views_dict[view_name]
                try:
                    # Start transaction in current_doc per view
                    trans_current = Transaction(current_doc, "Update Drafting View '{}'".format(view_name))
                    trans_current.Start()

                    # Delete existing elements in the current view
                    delete_elements_in_view(current_doc, current_view)
                    # Copy elements from master view to current view
                    copy_elements_from_master(current_doc, master_doc, master_view, current_view)

                    trans_current.Commit()
                    print("Drafting view '{}' has been updated from the master model.".format(view_name))
                except Exception as e:
                    trans_current.RollBack()
                    forms.alert(
                        "Failed to update drafting view '{}'.\nError: {}".format(view_name, e),
                        title="Error",
                        warn_icon=True
                    )
            else:
                forms.alert(
                    "Drafting view '{}' does not exist in the current document.".format(view_name),
                    title="Info",
                    warn_icon=False
                )
        # Commit transaction in master_doc after the loop
        trans_master.Commit()
    except Exception as e:
        trans_master.RollBack()
        forms.alert(
            "Failed to complete updating drafting views from master.\nError: {}".format(e),
            title="Error",
            warn_icon=True
        )

# Main function
def main():
    # Prompt user to select the master document
    master_path = forms.pick_file(file_ext='rvt', title="Select the Master Revit Document")
    if not master_path:
        forms.alert("No master document selected.", title="Cancelled", warn_icon=True)
        return

    master_doc = load_master_document(master_path)
    if not master_doc:
        return

    current_doc = revit.doc  # This is your current project document

    # Ensure master_doc and current_doc are not the same
    if not current_doc.PathName:
        forms.alert("Please save the current document before running this script.", title="Error", warn_icon=True)
        return

    if not master_doc.PathName:
        forms.alert("The master document has not been saved. Please save it before proceeding.", title="Error", warn_icon=True)
        return

    if master_doc.PathName == current_doc.PathName:
        forms.alert("Master document and current document are the same.", title="Error", warn_icon=True)
        return

    update_drafting_views_from_master(master_doc, current_doc)

    # Close the master document if it was opened by the script
    try:
        master_doc.Close(False)  # False to not save changes
    except Exception as e:
        print("Could not close master document: {}".format(e))

# Call the main function
if __name__ == "__main__":
    main()
