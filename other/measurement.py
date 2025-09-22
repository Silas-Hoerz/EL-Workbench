from other.info import InfoManager

def start(shared_data):
    """
    Startet den Messvorgang und sendet eine Info-Meldung.
    """

    shared_data.info_manager.status(InfoManager.INFO, "Whtas easdlfa")