function [imageStack,imageInfo,filePath] = loadImageStack(filePath,maxFrames,uiMesssage,uiType)
%%
% Author: Marcel Goldschen-Ohm
% Email: marcel.goldschen@gmail.com
%
% Load image stack from file.
%
% Handles both grayscale intensity images and RGB color images.
%
% Will automatically concatenate series of image stacks named as
%   myfile.tif
%   myfile-file002.tif
%   myfile-file003.tif
%   ...
%
% args:
% -----
% filePath:     Optional file path of image stack to be loaded.
%               If not exist or empty --> popup a file selection UI.
% maxFrames:    Optional max number of frames to read from stack.
%               If not exist or inf --> read all frames in stack.
% uiMesssage:	Optional message displayed in file selection UI.
%               If not exist or empty --> use default message.
% uiType:   	Optional type specifier in file selection UI.
%               If not exist or empty --> use '*.tif'.
%
% return:
% -------
% imageStack:   Grayscale: (rows x columns x frames) 3d array.
%               RGB Color: (rows x columns x RGB x frames) 4d array.
% imageInfo:    Struct array of info for each frame.

%% Init.
imageStack = [];
imageInfo = [];
if ~exist('filePath','var') filePath = ''; end
if isempty(filePath) || contains(filePath,'*')
    if ~exist('uiMesssage','var') || isempty(uiMesssage) uiMesssage = 'Load image stack.'; end
    if ~exist('uiType','var') || isempty(uiType) uiType = '*.tif'; end
    [file,path] = uigetfile(uiType,uiMesssage,filePath);
    if isequal(file,0)
        errordlg('ERROR: File not selected.');
        return
    end
    filePath = fullfile(path,file);
end
[path,file,ext] = fileparts(filePath);
if ~exist(filePath,'file')
    errordlg(['ERROR: File not found: ' filePath]);
    return
end
fileLabel = file;
fileLabel(strfind(fileLabel,'_')) = ' ';
if ~exist('maxFrames','var') maxFrames = inf; end

%% Start timer.
tic

%% Get some info about the image file.
imageInfo = imfinfo(filePath);
numFrames = numel(imageInfo);
if numFrames == 0
    errordlg('ERROR: Zero frames detected in image stack.');
    return
end
if (maxFrames > 0) && (maxFrames < numFrames)
    numFrames = maxFrames;
end
width = imageInfo(1).Width;
height = imageInfo(1).Height;
bpp = imageInfo(1).BitDepth;
color = imageInfo(1).ColorType;
infoStr = [num2str(width) 'x' num2str(height) 'x' num2str(numFrames) '@' num2str(bpp) ' ' color];
disp(['Loading ' infoStr ' image stack from ' filePath '...']);

%% Allocate memory for entire image stack.
frame = imread(filePath,1,'Info',imageInfo);
pixels = frame(:);
fmt = get(pixels(1),'format');
imageStack = zeros([size(frame) numFrames],fmt);
isMonochrome = length(size(frame)) == 2;
if isMonochrome
    imageStack(:,:,1) = frame;
else % RGB
    imageStack(:,:,:,1) = frame;
end

%% Load stack one frame at a time.
% !!! Updating waitbar is expensive, so do it sparingly.
wb = waitbar(0,[fileLabel ' (' infoStr ')']);
framesPerWaitbarUpdate = floor(double(numFrames)/20);
for frame = 2:numFrames
    if isMonochrome
        imageStack(:,:,frame) = imread(filePath,frame,'Info',imageInfo);
    else % RGB
        imageStack(:,:,:,frame) = imread(filePath,frame,'Info',imageInfo);
    end
    if mod(frame,framesPerWaitbarUpdate) == 0
        waitbar(double(frame)/numFrames,wb);
    end
end
close(wb);

%% Check for additional files belonging to this stack.
% e.g. myFile.tif, myFile-file002.tif, myFile-file003.tif, ...
if ~isinf(maxFrames) && maxFrames > 0
    maxFrames = maxFrames - numFrames;
end
if isinf(maxFrames) || maxFrames > 0
    if strcmp(file(end-7:end-3),'-file') % blah-file002
        fileNum = str2num(file(end-3:end));
        nextFilePath = fullfile(path,[file(1:end-3) num2str(fileNum+1,'%03u')],ext);
    else % blah (so next file would be blah-file002)
        nextFilePath = fullfile(path,[file '-file002'],ext);
    end
    if exist(nextFilePath,'file') == 2
        nextStack = loadImageStack(nextFilePath,'',maxFrames);
        imageStack = cat(length(size(imageStack)),imageStack,nextStack);
    end
end

%% Elapsed time.
toc
disp('... Finished loading image stack.');

end
