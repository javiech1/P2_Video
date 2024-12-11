import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from app import build_ffmpeg_command, convert_video, encode_ladder, CODECS, RESOLUTIONS, BITRATES
import subprocess

class TestVideoConverter(unittest.TestCase):
    def setUp(self):
        self.input_path = "test_input.mp4"
        self.output_path = "test_output.mp4"
        self.codec = "h265"
        self.resolution = "1920:1080"
        self.bitrate = "1000k"

    def test_build_ffmpeg_command(self):
        """Test FFmpeg command building"""
        expected_command = [
            'ffmpeg', '-i', self.input_path,
            '-vf', f'scale={self.resolution}',
            '-b:v', self.bitrate, '-y',
            '-c:v', 'libx265', '-preset', 'fast', '-c:a', 'aac', '-b:a', '128k',
            self.output_path
        ]
        
        command = build_ffmpeg_command(
            self.input_path, 
            self.output_path, 
            self.codec, 
            self.resolution, 
            self.bitrate
        )
        
        self.assertEqual(command, expected_command)

    def test_build_ffmpeg_command_all_codecs(self):
        """Test FFmpeg command building for all codecs"""
        for codec in CODECS:
            output = f"test_output{CODECS[codec]['ext']}"
            command = build_ffmpeg_command(
                self.input_path,
                output,
                codec,
                self.resolution,
                self.bitrate
            )
            
            self.assertIn('ffmpeg', command)
            self.assertIn('-i', command)
            self.assertIn(self.input_path, command)
            self.assertIn(output, command)
            for param in CODECS[codec]['params']:
                self.assertIn(param, command)

    @patch('subprocess.run')
    def test_convert_video_success(self, mock_run):
        """Test successful video conversion"""
        mock_run.return_value = MagicMock(returncode=0)
        
        success, result = convert_video(
            self.input_path,
            self.codec,
            self.resolution,
            self.bitrate
        )
        
        self.assertTrue(success)
        self.assertTrue(result.startswith('output_single'))
        self.assertTrue(result.endswith('.mp4'))
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_convert_video_failure(self, mock_run):
        """Test failed video conversion"""
        error_message = "FFmpeg error"
        mock_run.side_effect = subprocess.CalledProcessError(
            1, [], stderr=error_message
        )
        
        success, result = convert_video(
            self.input_path,
            self.codec,
            self.resolution,
            self.bitrate
        )
        
        self.assertFalse(success)
        self.assertEqual(result, error_message)
        mock_run.assert_called_once()

    @patch('app.convert_video')
    def test_encode_ladder(self, mock_convert):
        """Test encoding ladder generation"""
        mock_convert.return_value = (True, "test_output.mp4")
        
        results = encode_ladder(self.input_path, self.codec)
        
        self.assertEqual(len(results), len(RESOLUTIONS))
        self.assertEqual(len(results), len(BITRATES))
        mock_convert.assert_called()
        self.assertEqual(mock_convert.call_count, len(RESOLUTIONS))

    def test_invalid_codec(self):
        """Test handling of invalid codec"""
        with self.assertRaises(KeyError):
            build_ffmpeg_command(
                self.input_path,
                self.output_path,
                "invalid_codec",
                self.resolution,
                self.bitrate
            )

    @patch('subprocess.run')
    def test_output_path_format(self, mock_run):
        """Test output path formatting"""
        mock_run.return_value = MagicMock(returncode=0)
        
        for codec in CODECS:
            success, result = convert_video(
                self.input_path,
                codec,
                self.resolution,
                self.bitrate,
                is_single=True
            )
            
            # Check file extension
            self.assertTrue(result.endswith(CODECS[codec]['ext']))
            # Check prefix
            self.assertTrue(result.startswith('output_single'))
            # Check resolution format
            self.assertIn(self.resolution.replace(':', 'x'), result)
            # Check bitrate inclusion
            self.assertIn(self.bitrate, result)

if __name__ == '__main__':
    unittest.main() 