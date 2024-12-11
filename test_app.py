import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
from app import build_ffmpeg_command, convert_video, encode_ladder, CODECS, RESOLUTIONS, BITRATES

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

    def test_resolutions_and_bitrates_match(self):
        """Test that resolutions and bitrates arrays have matching lengths"""
        self.assertEqual(
            len(RESOLUTIONS), 
            len(BITRATES), 
            "Resolutions and bitrates arrays must have the same length"
        )

    def test_codec_configurations(self):
        """Test codec configuration validity"""
        for codec, config in CODECS.items():
            self.assertIn('ext', config, f"Codec {codec} missing 'ext' configuration")
            self.assertIn('params', config, f"Codec {codec} missing 'params' configuration")
            self.assertTrue(config['ext'].startswith('.'), f"Extension for {codec} should start with '.'")
            self.assertIsInstance(config['params'], list, f"Params for {codec} should be a list")
            self.assertTrue(len(config['params']) > 0, f"Params for {codec} should not be empty")

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

    def test_resolution_format(self):
        """Test resolution format validation"""
        invalid_resolutions = [
            "1920x1080",  # wrong separator
            "1920:",      # missing height
            ":1080",      # missing width
            "abcd:1080",  # invalid width
            "1920:efgh",  # invalid height
            "",          # empty string
        ]
        
        for resolution in invalid_resolutions:
            with self.subTest(resolution=resolution):
                with self.assertRaises(Exception):
                    build_ffmpeg_command(
                        self.input_path,
                        self.output_path,
                        self.codec,
                        resolution,
                        self.bitrate
                    )

    def test_bitrate_format(self):
        """Test bitrate format validation"""
        invalid_bitrates = [
            "1000",    # missing 'k'
            "abc",     # invalid characters
            "1000kb",  # wrong suffix
            "",       # empty string
        ]
        
        for bitrate in invalid_bitrates:
            with self.subTest(bitrate=bitrate):
                with self.assertRaises(Exception):
                    build_ffmpeg_command(
                        self.input_path,
                        self.output_path,
                        self.codec,
                        self.resolution,
                        bitrate
                    )

    @patch('app.convert_video')
    def test_encode_ladder(self, mock_convert):
        """Test encoding ladder generation"""
        mock_convert.return_value = (True, "test_output.mp4")
        
        results = encode_ladder(self.input_path, self.codec)
        
        self.assertEqual(len(results), len(RESOLUTIONS))
        self.assertEqual(len(results), len(BITRATES))
        mock_convert.assert_called()
        self.assertEqual(mock_convert.call_count, len(RESOLUTIONS))

    @patch('app.convert_video')
    def test_encode_ladder_partial_failure(self, mock_convert):
        """Test encoding ladder with some failed conversions"""
        returns = [
            (True, "success1.mp4"),
            (False, "error1"),
            (True, "success2.mp4"),
            (False, "error2")
        ]
        mock_convert.side_effect = returns
        
        results = encode_ladder(self.input_path, self.codec)
        
        self.assertEqual(len(results), len(returns))
        for (success, result), (exp_success, exp_result) in zip(results, returns):
            self.assertEqual(success, exp_success)
            self.assertEqual(result, exp_result)

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

    def test_path_handling(self):
        """Test path handling with different formats"""
        test_paths = [
            "input.mp4",
            "./input.mp4",
            "../input.mp4",
            "path/to/input.mp4",
            Path("input.mp4"),
            Path("path/to/input.mp4")
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                command = build_ffmpeg_command(
                    str(path),
                    self.output_path,
                    self.codec,
                    self.resolution,
                    self.bitrate
                )
                self.assertIn(str(path), command)

    @patch('subprocess.run')
    def test_empty_input_handling(self, mock_run):
        """Test handling of empty or None inputs"""
        invalid_inputs = [None, "", " "]
        
        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(ValueError):
                    convert_video(
                        invalid_input,
                        self.codec,
                        self.resolution,
                        self.bitrate
                    )

if __name__ == '__main__':
    unittest.main() 