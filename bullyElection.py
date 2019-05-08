import Pyro4
import os, time, random, sys
import threading

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class bullyElection(object):
	def __init__(self):
		self.pid 	= os.getpid()
		self.leader	= 0

	def getPID(self):
		return self.pid

	# Start a new election
	def startElection(self, electionPID = 0):
		verifyAlive = 0

		print('Starting a new election.')

		if electionPID and self.getPID() > electionPID:
			return 1

		for processPID in sorted(processThread.keys()):
			if processPID > self.getPID():
				try:
					if processThread[processPID].startElection(self.getPID()):
						verifyAlive = verifyAlive + 1
				except Exception as e:
					self.newArray(processPID)

		if not verifyAlive:
			print('Im the new leader')	
			for processPID in sorted(processThread.keys()):
				try:
					if processPID < self.getPID():
						processThread[processPID].setLeader(self.getPID())
					else:
						self.setLeader(self.getPID())
				except Exception as e:
					self.newArray(processPID)

	# Set a new leader
	def setLeader(self, processPID):
		self.leader = processPID
		print('New leader was set!')

	# Remove the selected process
	def newArray(self, processPID):
		print('Process ' + str(processPID) + ' is dead')
		del processThread[processPID]
		print('Removing process')
		print('New process array have ' + str(len(processThread)) + ' processes')

	# Return the leader PID
	def getLeader(self):
		return self.leader

	# Verify if the leader is alive, if not, start a new election
	def verifyLeader(self):
		try:
			processThread[self.getLeader()].isAlive()
		except Exception as e:
			print('Leader is dead!')
			self.startElection()

	def isAlive(self):
		return 1

class server():
	# Start a new server
	def enable(self):
		self.daemon = Pyro4.Daemon()
		self.uri 	= self.daemon.register(bullyElection)

		self.ns = Pyro4.locateNS()
		self.ns.register("process." + sys.argv[1], self.uri)

		self.thread = threading.Thread(target=self.daemonLoop)
		self.thread.start()
		print("Started thread")

	# Kill server
	def disable(self):
		print("Called for daemon shutdown")
		self.daemon.shutdown()

	# Start the daemon loop, pyro requires this call to server works
	def daemonLoop(self):
		self.daemon.requestLoop()
		print("Daemon has shut down no prob")

if __name__ == '__main__':
	# Create a new server and enable
	s = server()
	s.enable()

	# Set an array with five process already know
	time.sleep(10)
	processThread = {}

	processOne 		= Pyro4.Proxy("PYRONAME:process.one")
	processTwo 		= Pyro4.Proxy("PYRONAME:process.two")
	processThree 	= Pyro4.Proxy("PYRONAME:process.three")
	processFour 	= Pyro4.Proxy("PYRONAME:process.four")
	processFive 	= Pyro4.Proxy("PYRONAME:process.five")

	processThread.update({processOne.getPID():		processOne})
	processThread.update({processTwo.getPID():		processTwo})
	processThread.update({processThree.getPID():	processThree})
	processThread.update({processFour.getPID():		processFour})
	processThread.update({processFive.getPID():		processFive})

	actualProcess = processThread[os.getpid()]

	# Start a new election in 30-60 sec
	time.sleep(random.randint(30, 60))
	print('Starting election for the first time')
	actualProcess.startElection()

	# In a loop the client will print every 30 seconds the leader PID
	# After 5-10 messages the client will verify if the leader still up
	# If not, a new election will be started
	while(True):
		for i in range(1, random.randint(5, 10)):
			time.sleep(30)
			print('[' + str(actualProcess.getPID()) + '] Leader: ' + str(actualProcess.getLeader()))
		
		print('Verifying is Leader is alive')
		if actualProcess.getLeader() != actualProcess.getPID():
			actualProcess.verifyLeader()
