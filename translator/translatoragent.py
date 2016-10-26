from __future__ import absolute_import
from datetime import datetime
import logging
import sys
import json

from volttron.platform.vip.agent import Agent, Core, PubSub, compat
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod

from . import settings
utils.setup_logging()
_log = logging.getLogger(__name__)

class TranslatorAgent(Agent):
    
    
    def __init__(self, config_path, **kwargs):
        super(TranslatorAgent, self).__init__(**kwargs)
        self.config = utils.load_config(config_path)
        self._agent_id = self.config['agentid']
        
        _log.info(self.config['message'])
        self._agent_id = self.config['agentid']
        
    @Core.receiver('onstart')
    def setup(self, sender, **kwargs):
        _log.info(self.config['message'])
        self._agent_id = self.config['agentid']
        
        print('!!!HELLO!!! Translator Agent starting up and subscribing to topic: openADRevent')
        self.vip.pubsub.subscribe('pubsub','openADRevent', callback = self.OADRtoCTA)
    
    def OADRtoCTA(self, peer, sender, bus, topic, headers, message):
        try:
            mesdict = json.loads(message)
        except jsonDecodeError as e:
            print("JSON error of type <{type}>".format(type = e))
            
        eventID = mesdict.get("event_ID", 0)
        eventType = mesdict.get("event_type", "simple_signal")
        priority = int(mesdict.get("priority", 1))
        startTime = mesdict.get("start_time", "now")
        duration = mesdict.get("duration", 0).replace("S","")
        payload = int(mesdict.get("signalPayload",0))
        
        
        
        ctadict = {"message_subject": "new_event",
                   "message_target": "all",
                   "event_uid": str(eventID),
                   "priority": str(priority),
                   "ADR_start_time": startTime}
       
        if eventType == "simple_signal":            
            if payload == 0:
                ctadict["message_type"] = "normal"
                ctadict["event_name"] = "normal"
            elif payload == 1:
                ctadict["message_type"] = "shed"
                ctadict["event_name"] = "shed"
            elif payload == 2:
                ctadict["message_type"] = "critical_peak"
                ctadict["event_name"] = "critical_peak"
            elif payload == 3:
                ctadict["message_type"] = "grid_emergency"
                ctadict["event_name"] = "grid_emergency"
            elif payload == 4:
                ctadict["message_type"] = "load_up"
                ctadict["event_name"] = "load_up"
            else:
                print("translator agent received an unexpected payload value: {value}".format(value = payload))
        
            ctadict["event_duration"] = str(duration)     
        elif eventType == "load_control":
            ctadict["message_type"] = "temperature_offset"
        elif eventType == "energy_price":
            ctadict["message_type"] = "cur_price"
        elif eventType == "telemetry_status":
            ctadict["message_type"] = "comm_state"
        elif eventType == "custom_report":
            ctadict["message_type"]  = "query_op_state"
        
        ctamess = json.dumps(ctadict)
        print("Translator received {rec}...\n....and issued {sent}".format(rec = message, sent = ctamess))
        self.vip.pubsub.publish('pubsub','CTAevent',{}, ctamess)
       
def main(argv = sys.argv):
    '''Main method called by the eggsecutable'''
    try:
        utils.vip_main(TranslatorAgent)
    except Exception as e:
        _log.exception('unhandled exception')
            
if __name__== '__main__':
    #entry point for script_from_examples
    sys.exit(main())
