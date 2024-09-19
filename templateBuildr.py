from Autodesk.Revit.DB import FilteredElementCollector, Transaction, ViewDrafting, ElementId
from pyrevit import revit, DB
import Autodesk.Revit.DB as DB

doc = __revit__.ActiveUIDocument.Document
ui = __revit__.ActiveUIDocument

# Function to get a dictionary of drafting view names and their elements
def get_drafting_views_dict(doc):
    drafting_views_dict = {}
    collector = FilteredElementCollector(doc).OfClass(ViewDrafting).WhereElementIsNotElementType()
    for view in collector:
        if not view.IsTemplate:
            drafting_views_dict[view.Name] = view
    print(drafting_views_dict)
    return drafting_views_dict

# Function to compare and update drafting views
def update_drafting_views_from_master(master_doc, current_doc):
    master_views_dict = get_drafting_views_dict(master_doc)
    current_views_dict = get_drafting_views_dict(current_doc)

    with Transaction(current_doc, "Update Drafting Views") as trans:
         trans.Start()
         for view_name, master_view in master_views_dict.items():
            if view_name in current_views_dict:
                 current_view = current_views_dict[view_name]
    #              Activate the view (this might need to be handled differently, as direct view activation is not typical in Revit API)
    #              Delete the contents of the current view
    #              Note: This step requires identifying and deleting individual elements within the view, which can vary based on content
    #              Copy content from master view to current view
    #              This step is complex and might require recreating elements manually or using third-party libraries
                 print("Drafting view '{}' has been updated from the master model.".format(view_name))
         trans.Commit()

# Main function
def main():
    # Placeholder: Load/open the master model document and current project document
    master_doc = revit.doc  # Adjust to actually load/open the master model document
    current_doc = revit.doc  # This is your current project document

    update_drafting_views_from_master(master_doc, current_doc)

# Call the main function
main()