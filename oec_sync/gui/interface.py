"""
Midpoint between UI and backend
"""
from synchronizer import Synchronizer
from update_request import UpdateRequest, CachedRequest
from syncutil import SrcPath
from model import PlanetarySysUpdate


class Interface:
    """
    Provides methods callable from UI that interact with backend. Re-routes
    display to GUI
    """
    __local_requests = []
    __remote_requests = []
    __syncr = None
    __config = None

    @staticmethod
    def init(config: str):
        Interface.__config = config
        Interface.__syncr = Synchronizer(config)

    @staticmethod
    def get_syncr() -> Synchronizer:
        return Interface.__syncr

    @staticmethod
    def get_requests(type: str):
        result = []
        if type in ["remote", "local"]:
            if type == "local":
                result = Interface.__local_requests.copy()
            else:
                result = Interface.__remote_requests.copy()
        return result

    @staticmethod
    def sync(on_complete):
        requests = []

        def sync_callback(request: UpdateRequest):
            requests.append(request)

        Interface.get_syncr().sync(sync_callback)
        Interface.__local_requests = requests
        for key, value in Interface.get_syncr().db.requests.items():
            if isinstance(value, CachedRequest):
                Interface.__remote_requests.append(value.request)
        on_complete()

    @staticmethod
    def reject(idx: int):
        result = ("", "")
        if len(Interface.__local_requests) > 0 and \
                len(Interface.__local_requests) > idx:
            syncr = Interface.get_syncr()
            req = Interface.__local_requests[idx]
            syncr.reject(req)
            result = (("Closed Pull Request #%d" % req.pullreq_num),
                      ("%s" % req.pullreq_url))
        return result

    @staticmethod
    def get_system_from_index(i=0):
        return Interface.__local_requests[i].updates.name \
            if len(Interface.__local_requests) > 0 else None

    @staticmethod
    def delete_system_at_index(idx):
        if len(Interface.__local_requests) > 0 and \
                        len(Interface.__local_requests) > idx:
            Interface.__local_requests.pop(idx)
            Interface.populate_request_list()

    @staticmethod
    def find_system(name: str):
        j = 0
        idx = -1
        obj = None
        type_ = ""
        if name.startswith("remote-"):
            for req in Interface.__remote_requests:
                if "remote-"+req.updates.name == name:
                    idx = j
                    obj = req
                    type_ = "remote"
                    break
                j += 1
        else:
            for req in Interface.__local_requests:
                if "local-"+req.updates.name == name:
                    idx = j
                    obj = req
                    type_ = "local"
                    break
                j += 1
        return idx, obj, type_

    @staticmethod
    def get_all_systems(type: str):
        result = []
        if type == "remote":
            result = Interface.__remote_requests.copy()
        elif type == "local":
            result = Interface.__local_requests.copy()
        return result

    @staticmethod
    def send(idx: int, edit_func):
        result = ("", "")
        if len(Interface.__local_requests) > 0 and \
                len(Interface.__local_requests) > idx:
            syncr = Interface.get_syncr()
            req = Interface.__local_requests[idx]

            syncr.submit(Interface.__local_requests[idx], editor=edit_func)

            if req.pullreq_num > 0:
                result = (("Open Pull Request #%d" % req.pullreq_num),
                          ("%s" % req.pullreq_url))
        return result

    @staticmethod
    def populate_request_list():
        local_sys_names = []
        remote_sys_names = []
        if len(Interface.__local_requests) > 0:
            for req in Interface.__local_requests:
                local_sys_names.append("local-"+req.updates.name)
        if len(Interface.__remote_requests) > 0:
            for req in Interface.__remote_requests:
                remote_sys_names.append("remote-"+req.updates.name)
        return local_sys_names, remote_sys_names


if __name__ == "__main__":
    Interface.sync()
    Interface.populate_request_list()
