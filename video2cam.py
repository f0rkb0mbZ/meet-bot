import ffmpeg

def loop_video_to_v4l2(input_path: str, device: str = "/dev/video0"):
    (
        ffmpeg
        .input(input_path, stream_loop=-1, re=None)
        .output(device,
                vcodec='rawvideo',
                pix_fmt='yuv420p',
                f='v4l2')
        .run()
    )

if __name__ == "__main__":
    loop_video_to_v4l2("https://r2.snehangshu.dev/bot_say_hello.mp4")
