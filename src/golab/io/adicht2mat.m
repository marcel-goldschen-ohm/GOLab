% Requires ADInstruments (LabChart) SDK by Jim Hokanson
% Available in MATLAB Add-Ons or at https://github.com/JimHokanson/adinstruments_sdk_matlab
% !!! ONLY works on Windows !!!

adiFile = adi.readFile;

[path, file, ext] = fileparts(adiFile.file_path);
file_date = strrep(file(1:10), '_', '-');

IL = adiFile.getChannelByName('IL');
IR = adiFile.getChannelByName('IR');
VL = adiFile.getChannelByName('VL');
VR = adiFile.getChannelByName('VR');

for i = 1:adiFile.n_records
    data = struct;
    data.current = IL.getData(i);
    data.current_units = IL.units{i};
    data.voltage = VL.getData(i);
    data.voltage_units = VL.units{i};
    data.time_interval_sec = IL.dt(i);
    data.events = struct.empty;
    for j = 1:length(adiFile.records(i).comments)
        comment = adiFile.records(i).comments(j);
        if comment.channel == -1 || comment.channel == 0
            data.events(end+1).text = comment.str;
            data.events(end).time_sec = comment.time;
        end
    end
    filename = fullfile(path, [file '_L']);
    if adiFile.n_records > 1
        filename = [filename '_' num2str(i)];
    end
    save(filename, '-struct', 'data');

    data = struct;
    data.current = IR.getData(i);
    data.current_units = IR.units{i};
    data.voltage = VR.getData(i);
    data.voltage_units = VR.units{i};
    data.time_interval_sec = IR.dt(i);
    data.events = struct.empty;
    for j = 1:length(adiFile.records(i).comments)
        comment = adiFile.records(i).comments(j);
        if comment.channel == -1 || comment.channel == 2
            data.events(end+1).text = comment.str;
            data.events(end).time_sec = comment.time;
        end
    end
    filename = fullfile(path, [file '_R']);
    if adiFile.n_records > 1
        filename = [filename '_' num2str(i)];
    end
    save(filename, '-struct', 'data');
end
