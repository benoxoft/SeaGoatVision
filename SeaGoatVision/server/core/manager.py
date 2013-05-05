#! /usr/bin/env python

#    Copyright (C) 2012  Octets - octets.etsmtl.ca
#
#    This file is part of SeaGoatVision.
#
#    SeaGoatVision is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Description :
Authors: Benoit Paquet
         Mathieu Benoit <mathben963@gmail.com>
Date : Novembre 2012
"""

from SeaGoatVision.server import imageproviders
from SeaGoatVision.server.core.mainloop import MainLoop
from SeaGoatVision.server.tcp_server import Server
from configuration import Configuration
from SeaGoatVision.commun.keys import *

class Manager:
    def __init__(self):
        """
            Structure of dct_thread
            {"execution_name" : {"thread" : ref, "filterchain" : ref, "source_name" : str}}
        """
        self.dct_thread = {}
        self.config = Configuration()

        # tcp server for output observer
        self.server_observer = Server()
        self.server_observer.start("", 5030)
        self.last_record_source = None

    def close(self):
        print("Close manager")
        for thread in self.dct_thread.values():
            thread["thread"].quit()
        self.server_observer.stop()

    ##########################################################################
    ################################ CLIENT ##################################
    ##########################################################################
    def is_connected(self):
        return True

    ##########################################################################
    ############################# SERVER STATE ###############################
    ##########################################################################

    ##########################################################################
    ######################## EXECUTION FILTER ################################
    ##########################################################################
    def start_filterchain_execution(self, execution_name, source_name, filterchain_name):
        thread = self.dct_thread.get(execution_name, None)

        if thread:
            # change this, return the actual thread
            print("The execution %s is already created." % execution_name)
            return None

        source = imageproviders.load_sources().get(source_name, None)
        filterchain = self.config.get_filterchain(filterchain_name)

        if not(source and filterchain):
            print("Erreur with the source \"%s\" or the filterchain \"%s\". Maybe they dont exist."
                  % (source_name, filterchain_name))
            return None

        source = source()

        thread = MainLoop()
        thread.add_observer(filterchain.execute)
        thread.start(source)

        self.dct_thread[execution_name] = {"thread": thread, "filterchain": filterchain, "source_name" : source_name}

        return True

    def stop_filterchain_execution(self, execution_name):
        thread = self.dct_thread.get(execution_name, None)

        if not thread:
            # change this, return the actual thread
            print("The execution %s is already stopped." % execution_name)
            return None

        thread["thread"].quit()
        del self.dct_thread[execution_name]

        return True

    def get_execution_list(self):
        return self.dct_thread.keys()

    def get_execution_info(self, execution_name):
        exec_info = self.dct_thread.get(execution_name, None)
        if not exec_info:
            return None
        class Exec_info: pass
        o_exec_info = Exec_info()
        setattr(o_exec_info, "source", exec_info["source_name"])
        setattr(o_exec_info, "filterchain", exec_info["filterchain"].get_name())
        return o_exec_info

    ##########################################################################
    ################################ SOURCE ##################################
    ##########################################################################
    def get_source_list(self):
        # TODO improve me
        # return imageproviders.load_sources().keys()
        return {"Webcam":get_source_type_streaming_name(),
                "ImageSingle":get_source_type_video_name(),
                "Video":get_source_type_video_name(),
                "ImageFolder":get_source_type_video_name()}

    def start_record(self, source_name):
        # Only record on webcam device
        # TODO take the real instance of source and not this fake method
        if not self.dct_thread:
            return False
        dct = self.dct_thread.values()[0].get("thread", None)
        if not dct:
            return False
        source = dct.get_source()
        self.last_record_source = source
        return source.start_record()

    def stop_record(self, source_name):
        if not self.last_record_source:
            return False
        return self.last_record_source.stop_record()

    ##########################################################################
    ############################### THREAD  ##################################
    ##########################################################################

    ##########################################################################
    #############################  OBSERVER  #################################
    ##########################################################################
    def add_image_observer(self, observer, execution_name, filter_name):
        """
            Inform the server what filter we want to observe
            Param :
                - ref, observer is a reference on method for callback
                - string, execution_name to select an execution
                - string, filter_name to select the filter
        """
        ret_value = False
        dct_thread = self.dct_thread.get(execution_name, {})
        if dct_thread:
            filterchain = dct_thread.get("filterchain", None)
            if filterchain:
                ret_value = filterchain.add_image_observer(observer, filter_name)
        return ret_value

    def set_image_observer(self, observer, execution_name, filter_name_old, filter_name_new):
        """
            Inform the server what filter we want to change observer
            Param :
                - ref, observer is a reference on method for callback
                - string, execution_name to select an execution
                - string, filter_name_old , filter to replace
                - string, filter_name_new , filter to use
        """
        ret_value = False
        if filter_name_old != filter_name_new:
            dct_thread = self.dct_thread.get(execution_name, {})
            if dct_thread:
                filterchain = dct_thread.get("filterchain", None)
                if filterchain:
                    filterchain.remove_image_observer(observer, filter_name_old)
                    ret_value = filterchain.add_image_observer(observer, filter_name_new)
        return ret_value

    def remove_image_observer(self, observer, execution_name, filter_name):
        """
            Inform the server what filter we want to remove observer
            Param :
                - ref, observer is a reference on method for callback
                - string, execution_name to select an execution
                - string, filter_name , filter to remove
        """
        ret_value = False
        dct_thread = self.dct_thread.get(execution_name, {})
        if dct_thread:
            filterchain = dct_thread.get("filterchain", None)
            if filterchain:
                ret_value = filterchain.remove_image_observer(observer, filter_name)
        return ret_value

    def add_output_observer(self, execution_name):
        """
            attach the output information of execution to tcp_server
            supported only one observer. Add observer to tcp_server
        """
        ret_value = False
        dct_thread = self.dct_thread.get(execution_name, {})
        if dct_thread:
            filterchain = dct_thread.get("filterchain", None)
            if filterchain:
                if self.server_observer.send in filterchain.get_filter_output_observers():
                    return True
                ret_value = filterchain.add_filter_output_observer(self.server_observer.send)
        return ret_value

    def remove_output_observer(self, execution_name):
        """
            remove the output information of execution to tcp_server
            supported only one observer. remove observer to tcp_server
        """
        ret_value = False
        dct_thread = self.dct_thread.get(execution_name, {})
        if dct_thread:
            filterchain = dct_thread.get("filterchain", None)
            if filterchain:
                if not filterchain.get_filter_output_observers():
                    return True
                ret_value = filterchain.remove_filter_output_observer(self.server_observer.send)
        return ret_value

    ##########################################################################
    ########################## CONFIGURATION  ################################
    ##########################################################################
    def get_filterchain_list(self):
        return self.config.get_filterchain_list()

    def upload_filterchain(self, filterchain_name, s_file_contain):
        return self.config.upload_filterchain(filterchain_name, s_file_contain)

    def delete_filterchain(self, filterchain_name):
        return self.config.delete_filterchain(filterchain_name)

    def get_filter_list_from_filterchain(self, filterchain_name):
        return self.config.get_filters_from_filterchain(filterchain_name)

    def modify_filterchain(self, old_filterchain_name, new_filterchain_name, lst_str_filters):
        return self.config.modify_filterchain(old_filterchain_name, new_filterchain_name, lst_str_filters)

    ##########################################################################
    ############################ FILTERCHAIN  ################################
    ##########################################################################
    def reload_filter(self, filtre=None):
        for thread in self.dct_thread.values():
            filterchain = thread.get("filterchain", None)
            if filterchain:
                filterchain.reload_filter(filtre)

    def get_params_filterchain(self, execution_name, filter_name):
        # get actual filter from execution
        o_filter = None
        filterchain_item = None
        thread = self.dct_thread.get(execution_name, None)
        if not thread:
            return None
        filterchain = thread.get("filterchain", None)
        if not filterchain:
            return None
        # if filterchain_item is None:
        #    # search in config
        #    o_filter = self.config.get_filter_from_filterName(filter_name=filter_name)
        return filterchain.get_params(filter_name=filter_name)

    def update_param(self, execution_name, filter_name, param_name, value):
        dct_thread = self.dct_thread.get(execution_name, {})
        if not dct_thread:
            return None
        filterchain = dct_thread.get("filterchain", None)
        if not filterchain:
            return None
        filter = filterchain.get_filter(name=filter_name)
        param = filter.get_params(param_name=param_name)
        if param:
            param.set(value)
            filter.configure()
            return True
        return False

    ##########################################################################
    ############################### FILTER  ##################################
    ##########################################################################
    def get_filter_list(self):
        return self.config.get_filter_name_list()