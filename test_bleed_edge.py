import unittest
import os
import tempfile
import shutil
import numpy as np
from PIL import Image
import app

class TestBleedEdgeGeneration(unittest.TestCase):
    """Test class for verifying bleeding edge generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_output_dir = tempfile.mkdtemp()
        self.assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_output_dir):
            shutil.rmtree(self.test_output_dir)
    
    def get_bleed_region_pixels(self, output_img_path):
        """Extract pixels from the bleed region of the output image."""
        with Image.open(output_img_path) as img:
            img = img.convert('RGB')
            pixels = np.array(img)
            
            top_bleed = pixels[0:app.BLEED_LENGTH, :]
            bottom_bleed = pixels[-app.BLEED_LENGTH:, :]
            left_bleed = pixels[app.BLEED_LENGTH:-app.BLEED_LENGTH, 0:app.BLEED_LENGTH]
            right_bleed = pixels[app.BLEED_LENGTH:-app.BLEED_LENGTH, -app.BLEED_LENGTH:]
            
            bleed_pixels = np.concatenate([
                top_bleed.reshape(-1, 3),
                bottom_bleed.reshape(-1, 3),
                left_bleed.reshape(-1, 3),
                right_bleed.reshape(-1, 3)
            ], axis=0)
            
        return bleed_pixels
    
    def verify_simple_technique(self, output_img_path):
        """Verify that SIMPLE technique was used (uniform black bleed region)."""
        bleed_pixels = self.get_bleed_region_pixels(output_img_path)
        
        std_per_channel = np.std(bleed_pixels, axis=0)
        avg_std = np.mean(std_per_channel)
        self.assertLess(avg_std, 15, 
                       "SIMPLE technique should produce uniform bleed region")
        
        black_threshold = 30
        is_black = np.all(bleed_pixels <= black_threshold, axis=1)
        black_percent = np.mean(is_black)
        self.assertGreaterEqual(black_percent, 0.95,
                               "SIMPLE technique should produce black bleed region")
    
    def verify_replicate_technique(self, output_img_path, original_img_path):
        """Verify that REPLICATE technique was used (varied, non-uniform bleed region)."""
        bleed_pixels = self.get_bleed_region_pixels(output_img_path)
        
        std_per_channel = np.std(bleed_pixels, axis=0)
        avg_std = np.mean(std_per_channel)
        
        black_threshold = 30
        is_black = np.all(bleed_pixels <= black_threshold, axis=1)
        black_percent = np.mean(is_black)
        
        if black_percent > 0.95:
            self.assertGreater(avg_std, 10,
                             "REPLICATE technique should NOT produce uniform black bleed region")
        
        non_black_pixels = bleed_pixels[np.any(bleed_pixels > black_threshold, axis=1)]
        if len(non_black_pixels) > 0:
            non_black_std = np.std(non_black_pixels, axis=0)
            non_black_avg_std = np.mean(non_black_std)
            self.assertGreater(non_black_avg_std, 5,
                             "REPLICATE technique should replicate varied image edges")
    
    def test_fullart_uses_replicate(self):
        """Test that fullart card uses REPLICATE technique."""
        test_img_path = os.path.join(self.assets_dir, 'Lightning Bolt_Fullart_test.png')
        self.assertTrue(os.path.exists(test_img_path),
                       f"Test image not found: {test_img_path}")
        
        resized_path = app.resizeImg(test_img_path, output_dir=self.test_output_dir)
        expected_technique, _ = app.determineEdgeTechnique(resized_path)
        self.assertEqual(expected_technique, app.Edge.REPLICATE,
                        "Fullart card should use REPLICATE technique")
        
        output_path = app.addBleedEdge(resized_path, output_dir=self.test_output_dir)
        self.assertTrue(os.path.exists(output_path),
                       "Output image should be created")
        
        self.verify_replicate_technique(output_path, resized_path)
    
    def test_default_uses_simple(self):
        """Test that default/black border card uses SIMPLE technique."""
        test_img_path = os.path.join(self.assets_dir, 'Lightning Bolt_Default_test.png')
        self.assertTrue(os.path.exists(test_img_path),
                       f"Test image not found: {test_img_path}")
        
        resized_path = app.resizeImg(test_img_path, output_dir=self.test_output_dir)
        expected_technique, _ = app.determineEdgeTechnique(resized_path)
        self.assertEqual(expected_technique, app.Edge.SIMPLE,
                        "Default/black border card should use SIMPLE technique")
        
        output_path = app.addBleedEdge(resized_path, output_dir=self.test_output_dir)
        self.assertTrue(os.path.exists(output_path),
                       "Output image should be created")
        
        self.verify_simple_technique(output_path)

if __name__ == '__main__':
    unittest.main()
