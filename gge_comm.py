import socket
import multiprocessing
import queue
from threading import Thread
import threading
from gge_utils import log, decode2
import traceback
import sys
import time

BUFFER_SIZE = 2048
TIMEOUT = 10

class Processor:
    def __init__(self, config):
        self.queues = {}
        self.q_rsc = queue.Queue(TIMEOUT)
        self.q_txi = queue.Queue(TIMEOUT)
        self.q_txs = queue.Queue(TIMEOUT)
        self.q_txc = queue.Queue(TIMEOUT)
        self.q_gbd = queue.Queue(TIMEOUT)
        self.q_jaa = queue.Queue(TIMEOUT)
        self.q_gui = queue.Queue(TIMEOUT)  # Build Tools/Recruit troops info
        self.q_bup = queue.Queue(TIMEOUT)  # Execute build Tools/Recruit troops
        self.q_gaa = queue.Queue(TIMEOUT)
        self.q_abi = queue.Queue(TIMEOUT)  # Get info on fortress (tested in desert until now)
        self.q_aci = queue.Queue(TIMEOUT)  # Get info on (human) player's castle
        self.q_adi = queue.Queue(TIMEOUT)  # Get info on RBC
        self.q_pin = queue.Queue(TIMEOUT)
        self.q_cra = queue.Queue(TIMEOUT)  # Attack
        self.q_sbp = queue.Queue(TIMEOUT)  # Buy Tools from Armorer
        self.q_cmi = queue.Queue(TIMEOUT)  # Send RSS setup
        self.q_dcl = queue.Queue(TIMEOUT)  # Send RSS setup
        self.q_crm = queue.Queue(TIMEOUT)  # Send RSS
        self.q_mus = queue.Queue(TIMEOUT)
        self.q_gam = queue.Queue(TIMEOUT)  # Travelling Barrows
        self.q_ahh = queue.Queue(TIMEOUT)  # Ask for help
        self.q_pin = queue.Queue(TIMEOUT)
        self.q_aha = queue.Queue(TIMEOUT)  # Help All (perhaps help 1 as well???)
        self.q_hgh = queue.Queue(TIMEOUT)  # Player rankings / Player rankings search / Alliance ranking / Alliance ranking search
        self.q_gdi = queue.Queue(TIMEOUT)  # Get player's castle list/info
        self.q_clb = queue.Queue(TIMEOUT)  # Daily bonus (3x3 grid) (in response to a selection request)
        self.q_alb = queue.Queue(TIMEOUT)  # Daily bonus consumed
        self.q_hru = queue.Queue(TIMEOUT)  # Heal troops in the hospital
        self.q_hdu = queue.Queue(TIMEOUT)  # Delete troops from the hospital
        self.q_ssi = queue.Queue(TIMEOUT)  # Spies status/availability
        self.q_csm = queue.Queue(TIMEOUT)  # Send spies
        self.q_sne = queue.Queue(TIMEOUT)  # Receive message (not sure if this is only spy reports)????
        self.q_bsd = queue.Queue(TIMEOUT)  # Spy report content
        self.q_ain = queue.Queue(TIMEOUT)  # ????Alliance or Player info not sure anymore???
        self.q_tmp = queue.Queue(TIMEOUT)  # Blade Coast info
        self.q_sje = queue.Queue(TIMEOUT)  # Blade Coast related (don't know what it does)
        self.q_grc = queue.Queue(TIMEOUT)  # Blade Coast related (don't know what it does)
        self.q_tai = queue.Queue(TIMEOUT)  # Blade Coast get Target Info
        self.q_thm = queue.Queue(TIMEOUT)  # Blade Coast attack
        self.q_cat = queue.Queue(TIMEOUT)  # Station troops at one of your castles (not support)
        self.q_sti = queue.Queue(TIMEOUT)  # Get info to station troops at one of your castles (not support)
        self.q_rbu = queue.Queue(TIMEOUT)  # Repair building
        self.q_aqi = queue.Queue(TIMEOUT)  # Leave alliance
        self.q_saa = queue.Queue(TIMEOUT)  # Apply to alliance
        self.q_ggm = queue.Queue(TIMEOUT)  # Get Gems Info
        self.q_gli = queue.Queue(TIMEOUT)  # Get Commanders and Castlellans Info
        self.q_gei = queue.Queue(TIMEOUT)  # Get EQ Info
        self.q_msd = queue.Queue(TIMEOUT)  # Apply time boost
        self.q_fnt = queue.Queue(TIMEOUT)  # Find next tower (Berimond)
        self.q_pub = queue.Queue(TIMEOUT)  # Catchall queue

        self.queues["%xt%rsc%"] = self.q_rsc
        self.queues["%xt%txi%"] = self.q_txi
        self.queues["%xt%txs%"] = self.q_txs
        self.queues["%xt%txc%"] = self.q_txc
        self.queues["%xt%gbd%"] = self.q_gbd
        self.queues["%xt%jaa%"] = self.q_jaa
        self.queues["%xt%gui%"] = self.q_gui
        self.queues["%xt%bup%"] = self.q_bup
        self.queues["%xt%gaa%"] = self.q_gaa
        self.queues["%xt%abi%"] = self.q_abi
        self.queues["%xt%aci%"] = self.q_aci
        self.queues["%xt%adi%"] = self.q_adi
        self.queues["%xt%pin%"] = self.q_pin
        self.queues["%xt%cra%"] = self.q_cra
        self.queues["%xt%sbp%"] = self.q_sbp
        self.queues["%xt%cmi%"] = self.q_cmi
        self.queues["%xt%dcl%"] = self.q_dcl
        self.queues["%xt%crm%"] = self.q_crm
        self.queues["%xt%mus%"] = self.q_mus
        self.queues["%xt%gam%"] = self.q_gam
        self.queues["%xt%ahh%"] = self.q_ahh
        self.queues["%xt%pin%"] = self.q_pin
        self.queues["%xt%aha%"] = self.q_aha
        self.queues["%xt%hgh%"] = self.q_hgh
        self.queues["%xt%gdi%"] = self.q_gdi
        self.queues["%xt%clb%"] = self.q_clb
        self.queues["%xt%alb%"] = self.q_alb
        self.queues["%xt%hru%"] = self.q_hru
        self.queues["%xt%hdu%"] = self.q_hdu
        self.queues["%xt%ssi%"] = self.q_ssi
        self.queues["%xt%csm%"] = self.q_csm
        self.queues["%xt%sne%"] = self.q_sne
        self.queues["%xt%bsd%"] = self.q_bsd
        self.queues["%xt%ain%"] = self.q_ain
        self.queues["%xt%tmp%"] = self.q_tmp
        self.queues["%xt%sje%"] = self.q_sje
        self.queues["%xt%grc%"] = self.q_grc
        self.queues["%xt%tai%"] = self.q_tai
        self.queues["%xt%thm%"] = self.q_thm
        self.queues["%xt%cat%"] = self.q_cat
        self.queues["%xt%sti%"] = self.q_sti
        self.queues["%xt%rbu%"] = self.q_rbu
        self.queues["%xt%aqi%"] = self.q_aqi
        self.queues["%xt%saa%"] = self.q_saa
        self.queues["%xt%ggm%"] = self.q_ggm
        self.queues["%xt%gli%"] = self.q_gli
        self.queues["%xt%gei%"] = self.q_gei
        self.queues["%xt%msd%"] = self.q_msd
        self.queues["%xt%fnt%"] = self.q_fnt

        self.q = queue.Queue(TIMEOUT)  # Communication Queue between receiver & message dispatcher, all received messaged pass through it
        self._stop = False
        self._socket = None
        self.ini = config
        self.RSC = ''

    def execute(self, command):
        command.execute(self)

    def _rscUpdater(self):
        done = False
        while not done:
            data = self.q_rsc.get()
            if "xxkill" in data:  # if someone actually types this in chat and we grep for it in data we end up shutting down so I changed it from kill to xxkill for now ... neeed better fix
                done = 1
            else:
                decoded = decode2(data)
                self.RSC = str(decoded['RS'])
                log("RSC updated to " + self.RSC)

    #
    # Callback for Commands
    #
    def sendMessage(self, msg):
        # log(">>> sending: " + msg)
        sent = self._socket.send(msg.encode())
        if sent == 0:
            raise RuntimeError("socket connection broken")
        else:
            print ("sendmessage")

    #
    # Callback for Commands
    #
    def readResult(self):
        data = self.q_pub.get()
        log("readResult: " + data)
        return data

    def start(self):
        log("Processor Start")
        self._stop = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self.ini['Server.host'], int(self.ini['Server.port'])))
        p_receiver = Thread(target=self._receiver, args=(), name="RECEIVER THREAD")
        p_process = Thread(target=self._messageDispatcher, args=(), name="PROCESSOR THREAD")
        p_rsc_updater = Thread(target=self._rscUpdater, args=(), name="RSC UPDATER THREAD")
        p_process.start()
        p_receiver.start()
        p_rsc_updater.start()

    def stop(self):
        log("stop IN " + threading.current_thread().name)
        self._stop = True
        self._closeSocket()
        self.q.put('')

    def _receiver(self):
        try:
            while not self._stop:
                data = self._socket.recv(BUFFER_SIZE).decode()
                result = data
                lastByte = ":".join("{:02x}".format(ord(c)) for c in data[len(data) - 1:])
                while lastByte != "00" and not self._stop:
                    # log("RECEIVER READING SOCKET")
                    data = self._socket.recv(BUFFER_SIZE).decode()
                    # log("RECEIVER DONE READING SOCKET")
                    result = result + data
                    lastByte = ":".join("{:02x}".format(ord(c)) for c in data[len(data) - 1:])
                if not self._stop:  # If stop is set it means we're shutting down normally, if this is not checked here then we'll try to put a message in a closed queue since the processor already had time to cleanup everything
                    self.q.put(result)
        except:
            # traceback.print_exc(file=sys.stdout)
            log("GOT EXCEPTION IN _receiver, _stop=" + str(self._stop) + " " + traceback.format_exc())

        if not self._stop:  # We hit an exception in here stop everything
            log("debug - _receiver calling stop")
            self.stop()
        else:
            self._closeSocket()
        log("RECEIVER TERMINATED")

    def _closeSocket(self):
        log("RECEIVER _closeSocket IN")
        if self._socket is not None:
            log("RECEIVER _closeSocket performing cleanup")
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except:
                log("RECEIVER socket shutdown exception " + traceback.format_exc())

            try:
                self._socket.close()
            except:
                log("RECEIVER socket close exception " + traceback.format_exc())

            self._socket = None
        log("RECEIVER _closeSocket OUT")

    def _messageDispatcher(self):
        exit = 0
        while not exit:
            data = self.q.get()
            if len(data) == 0:
                log("<<< Received EMPTY TERMINATION message")
                self._dispatchMessage("xxkill")
                exit = 1
            elif "\0" in data:
                split = data.split("\0")
                for msg in split:
                    if len(msg) > 0:
                        # log("<<< Received message, len: " + str(len(msg)) + ": " + msg + "\n")
                        self._dispatchMessage(msg)
            else:
                # log("<<< Received message, len: " + str(len(data)) + ": " + data + "\n")
                self._dispatchMessage(data)
        log("_messageDispatcher TERMINATED")

    def _dispatchMessage(self, msg):
        try:
            for key in self.queues:
                if (key in msg):
                    self.queues[key].put(msg)
                    return

            if "xxkill" in msg:  # if someone actually types this in chat and we grep for it in data we end up shutting down so I changed it from kill to xxkill for now ... neeed better fix
                log("_dispatchMessage IN with xxkill")
                self.queues["%xt%rsc%"].put("xxkill")
                self._closeQueues()
            else:  # catchall
                self.q_pub.put(msg)
        except:
            log("_dispatchMessage " + traceback.format_exc())

    def _closeQueues(self):
        try:
            log("_closeQueues IN")
            # printThreads()

            time.sleep(5)

            # I don't know which damn queue has a message in it (could be any of them)
            # On windows the process cannot terminate when there is a queue that still has a message in it because the queue's inner
            # thread(s) remains alive and is a non demon thread (or is stuck on a blocking pipe IO operation, not sure anymore, see code...)
            for key in self.queues:
                log("Attempting to close Q {}".format(str(key)))
                self.queues[key].close()
                log("Successfuly closed Q {}".format(str(key)))
            log("Attempting to close Q q_pub")
            self.q_pub.close()
            log("Successfuly closed Q q_pub")
            log("Attempting to close Q q (base Q)")
            self.q.close()
            log("Successfuly closed Q q (base Q)")
            # printThreads()
        except:
            log("_closeQueues " + traceback.format_exc())
        log("_closeQueues OUT")
