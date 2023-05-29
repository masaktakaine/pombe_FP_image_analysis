# 分裂酵母Ade4-mNG顆粒のnd2ファイル、バッチ処理用
# Ch1: 緑色蛍光, 11 z-slices
# Ch2: 位相差像 100倍、1 z-slice
# nd2ファイルを開き、BackGround subtraction, Max Intensity projection, もう一度Background subtraction, 
# ガウシアンフィルタ処理、Ch1をマゼンタ、Ch2をシアン
#2023.5.27

from ij import IJ, ImagePlus, Prefs
from ij.process import ImageConverter
from ij import LookUpTable
from ij import WindowManager as WM
from ij.process import ImageStatistics as IS
options = IS.MEAN | IS.AREA | IS.STD_DEV
from ij.gui import Roi
from ij.plugin.frame import RoiManager as RM
from ij.measure import ResultsTable
from ij.measure import Measurements as ms
#options_is = IS.MEAN | IS.MEDIAN | IS.MODE
#options_imp = ImagePlus.MEAN | ImagePlus.MEDIAN | ImagePlus.MODE
options_ms = ms.MEAN | ms.MEDIAN | ms.MODE
import os
from os import path
from ij.plugin import ChannelSplitter as CS
from ij.plugin import RGBStackMerge, RGBStackConverter
from ij.plugin import Duplicator
from ij.plugin import ZProjector as ZP
from ij.plugin.filter import GaussianBlur
from ij.plugin.filter import BackgroundSubtracter as BS
createBackground = False
lightBackground = False
useParaboloid = False
doPresmooth = False
correctCorners = False

from ij.plugin import Concatenator
from ij.plugin import HyperStackConverter
from ij.plugin.filter import GaussianBlur
from ij.plugin.filter import Analyzer
from ij.plugin.filter import ParticleAnalyzer as PA
options_pa = PA.SHOW_NONE + PA.CLEAR_WORKSHEET+PA.ADD_TO_MANAGER # +PA.EXCLUDE_EDGE_PARTICLES + PA.SHOW_RESULTS+PA.SHOW_OUTLINES

from ij.plugin.filter import MaximumFinder
outputType = MaximumFinder.COUNT
excludeOnEdges = False

#@ String(label="Date of experiments, e.g., 2020-08-22") edate1
#@ File (label="Choose source Folder", style="directory") dirS0
#@ File (label="Choose destination Folder", style="directory") dirD0

def process_2ch_nd2(imp, radius, sigma):
	title = imp.getTitle().split(".")[0] # 拡張子無しのファイル名を取得、ピリオドで分割して前の要素を取る
	ch1 = CS.split(imp)[0] # ch1を抽出
	ch2 = CS.split(imp)[1] # ch2を抽出
# 位相差像をMax intensity projection、これ以降は処理しない
	ch2_mip = ZP.run(ch2, "max all")

# Ch1, 緑色蛍光像の処理	
# 1回目のBackGround subtraction, BSは2D画像一枚しか処理しないので、forループでstack全体を処理
#	radius = 25
	bs = BS()
	for j in range(ch1.getStackSize()):
			bs.rollingBallBackground(ch1.getStack().getProcessor(j+1), radius, createBackground, lightBackground, useParaboloid, doPresmooth, correctCorners)
	ch1_mip = ZP.run(ch1, "max all")
	# 2nd BG subtraction
	bs.rollingBallBackground(ch1_mip.getProcessor(), radius, createBackground, lightBackground, useParaboloid, doPresmooth, correctCorners)
#	ガウシアンフィルタ処理
	gb = GaussianBlur()
#	sigma = 0.5
	accuracy = 0.01
	gb.blurGaussian(ch1_mip.getProcessor(), sigma, sigma, accuracy)  # xとyのsigma
#   LUTをグレーにしておかないとMergeした後にマゼンタにならない
	IJ.run(ch1_mip, "Grays", "")
	IJ.run(ch1_mip, "Enhance Contrast...", "saturated=0.35")
	merge_cm = RGBStackMerge.mergeChannels([None, None, None, None, ch2_mip, ch1_mip, None], True)
	#RGBStackConverter.convertToRGB(merge_cm) # 戻り値無し
	return ch1_mip, ch2_mip, merge_cm, title

# Save the image file in tiff format
def save_image_as_tif(directory, filename, image):
    outputfile = os.path.join(directory, filename + ".tif")
    IJ.saveAs(image, "TIFF", outputfile) # 保存する画像、tiff形式、パスを指定
    
# Main code
# Make directories
edate = " "+edate1
# Make directories
dirD = os.path.join(str(dirD0), edate1 + "_output")
if not os.path.exists(dirD):
	os.mkdir(dirD)
dirBF = os.path.join(str(dirD), "BF")
if not os.path.exists(dirBF):
	os.mkdir(dirBF)                           
dirGreen = os.path.join(str(dirD), "Green")
if not os.path.exists(dirGreen):
	os.mkdir(dirGreen)
	#Create a folder for merge image
dirMerge = os.path.join(str(dirD), "merge")
if not os.path.exists(dirMerge):
	os.mkdir(dirMerge)

# os.listdirでファイルのリストを取得、str型にする必要あり
filelist = os.listdir(str(dirS0))
# リスト内包表記、nd2ファイルだけを抽出する、split(".")でピリオドの前後２つの単語に分かれる、[-1]は後ろの単語（=拡張子）を表す、[1]にしても同じ
nd2_files = [f for f in filelist if f.split(".")[-1] == "nd2"]
nd2_files = sorted(nd2_files)

for nd2_file in nd2_files:
	current_file_path = os.path.join(str(dirS0), nd2_file) # ファイルのパスを取得
	imp = IJ.openImage(current_file_path) 		# Create a ImagePlus object, assign it into imp
	results = process_2ch_nd2(imp, 25, 0.5)
	ch1_mip = results[0] 
	ch2_mip = results[1]
	merge_cm = results[2]   
	filename = results[3]    
	save_image_as_tif(str(dirGreen), filename, ch1_mip)
	save_image_as_tif(str(dirBF), filename, ch2_mip)
	save_image_as_tif(str(dirMerge), filename, merge_cm)

print "Done. \n"
IJ.run("Close All")