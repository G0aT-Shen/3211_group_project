// Authoring-only MP4 encoder using macOS AVFoundation (no application dependency).
import Foundation
import AVFoundation
import AppKit
import CoreVideo

struct Frame: Decodable { let path: String; let seconds: Int }
let manifest = URL(fileURLWithPath: CommandLine.arguments[1])
let output = URL(fileURLWithPath: CommandLine.arguments[2])
let frames = try JSONDecoder().decode([Frame].self, from: Data(contentsOf: manifest))
let writer = try AVAssetWriter(outputURL: output, fileType: .mp4)
let input = AVAssetWriterInput(mediaType: .video, outputSettings: [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey:1600, AVVideoHeightKey:1000])
input.expectsMediaDataInRealTime = false
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32ARGB, kCVPixelBufferWidthKey as String:1600, kCVPixelBufferHeightKey as String:1000])
writer.add(input)
guard writer.startWriting() else { fatalError("Cannot start writer: \(String(describing: writer.error))") }
writer.startSession(atSourceTime:.zero)
var tick: Int64 = 0
for frame in frames {
    guard let image = NSImage(contentsOfFile:frame.path), let cg=image.cgImage(forProposedRect:nil,context:nil,hints:nil) else { fatalError("Missing frame") }
    var pixel: CVPixelBuffer?
    CVPixelBufferCreate(kCFAllocatorDefault,1600,1000,kCVPixelFormatType_32ARGB,nil,&pixel)
    guard let buffer=pixel else { fatalError("Buffer allocation failed") }
    CVPixelBufferLockBaseAddress(buffer,[])
    let context=CGContext(data:CVPixelBufferGetBaseAddress(buffer),width:1600,height:1000,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(buffer),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipFirst.rawValue)!
    context.draw(cg,in:CGRect(x:0,y:0,width:1600,height:1000))
    CVPixelBufferUnlockBaseAddress(buffer,[])
    for _ in 0..<(frame.seconds*2) {
        while !input.isReadyForMoreMediaData { Thread.sleep(forTimeInterval:0.01) }
        guard adaptor.append(buffer,withPresentationTime:CMTime(value:tick,timescale:2)) else { fatalError("Append failed") }
        tick += 1
    }
}
writer.endSession(atSourceTime:CMTime(value:tick,timescale:2))
input.markAsFinished()
let signal=DispatchSemaphore(value:0)
writer.finishWriting { signal.signal() }
signal.wait()
guard writer.status == .completed else { fatalError("Writer failed: \(String(describing:writer.error))") }
let asset=AVURLAsset(url:output)
print("MP4 written: \(output.path), duration: \(CMTimeGetSeconds(asset.duration)) seconds")
