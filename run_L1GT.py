import FWCore.ParameterSet.Config as cms

from Configuration.Eras.Era_Run3_cff import Run3
process = cms.Process('TEST', Run3)

# Load standard configurations
process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')

# Set global tag for Run 3
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, '140X_dataRun3_HLT_v3', '')

# Process a few events
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(100))  # Adjust number of events

# Define RAW data source (Change file if needed)
process.source = cms.Source('PoolSource',
    fileNames = cms.untracked.vstring(
        'file:/eos/user/d/dadeveta/L1OfflineTrigger/input/9cd73531-173f-421c-8135-ab698159f294.root'
    )
)

# Function to unpack and repack L1 trigger data with parameters
def unpackAndRepackL1uGT(process, inputLabel, unpackedLabel, repackedLabel):
    # Unpack RAW data into digi format
    setattr(process, unpackedLabel, cms.EDProducer('L1TRawToDigi',
        InputLabel = cms.InputTag(inputLabel),
        FedIds = cms.vint32(1404),  # FED ID for L1GT
        Setup = cms.string('stage2::GTSetup')
    ))
    
    # Repack digi into RAW format with input tag parameters
    setattr(process, repackedLabel, cms.EDProducer('L1TDigiToRaw',
        GtInputTag = cms.InputTag(unpackedLabel),
        ExtInputTag = cms.InputTag(unpackedLabel),
        MuonInputTag = cms.InputTag(unpackedLabel, 'Muon'),
        ShowerInputLabel = cms.InputTag(unpackedLabel, 'MuonShower'),
        EGammaInputTag = cms.InputTag(unpackedLabel, 'EGamma'),
        JetInputTag = cms.InputTag(unpackedLabel, 'Jet'),
        TauInputTag = cms.InputTag(unpackedLabel, 'Tau'),
        EtSumInputTag = cms.InputTag(unpackedLabel, 'EtSum'),
        # Removed EtSumZDCInputTag, not allowed in this CMSSW 14_0_0?!.
        Setup = cms.string('stage2::GTSetup'),
        FedId = cms.int32(1404)
    ))
    
    return process

# Unpack raw data selector
process.l1tGtStage2RawData0 = cms.EDProducer('EvFFEDSelector',
    inputTag = cms.InputTag('rawDataCollector'),
    fedList = cms.vuint32(1404)
)

# Apply unpack-repack twice for validation
process = unpackAndRepackL1uGT(process, 'l1tGtStage2RawData0', 'l1tGtStage2Digis1', 'l1tGtStage2RawData1')
process = unpackAndRepackL1uGT(process, 'l1tGtStage2RawData1', 'l1tGtStage2Digis2', 'l1tGtStage2RawData2')

# Load L1 Global Trigger Emulator (using gtDigis)
process.load("L1Trigger.GlobalTrigger.gtDigis_cfi")
process.gtDigis.RawInputTag = cms.InputTag("l1tGtStage2Digis2")

# Define processing sequence
process.seq = cms.Sequence(
    process.l1tGtStage2RawData0 +
    process.l1tGtStage2Digis1 +
    process.l1tGtStage2RawData1 +
    process.l1tGtStage2Digis2 +
    process.l1tGtStage2RawData2 +
    process.gtDigis  # Run the emulator
)

# Run everything in a path
process.path = cms.Path(process.seq)

# Save output
process.output = cms.OutputModule('PoolOutputModule',
    fileName = cms.untracked.string('file:L1GT_output.root'),
    outputCommands = cms.untracked.vstring(
        'drop *',
        'keep *_rawDataCollector_*_*',
        'keep *_l1tGtStage2RawData*_*_*',
        'keep *_l1tGtStage2Digis*_*_*',
        'keep *_gtDigis_*_*'
    )
)

process.endpath = cms.EndPath(process.output)

